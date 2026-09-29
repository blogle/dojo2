#!/usr/bin/env python3
"""Pure release policy and changelog helpers used by GitHub workflows."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
BUMP_TYPES = frozenset({"patch", "minor", "major", "none"})
DIRECTIVE_PATTERN = re.compile(
    r"(?im)^[ \t]*\[release:(patch|minor|major|none)\][ \t]*$"
)
DIRECTIVE_MARKER_PATTERN = re.compile(r"(?im)^[ \t]*\[release:")
GENERATED_START = "<!-- BEGIN GENERATED RELEASES -->"
GENERATED_END = "<!-- END GENERATED RELEASES -->"
GENERATED_SECTION_PATTERN = re.compile(
    r"(?ms)^## (v\d+\.\d+\.\d+)(?: - \d{4}-\d{2}-\d{2})?\s*\n(.*?)(?=^## |\Z)"
)
LEGACY_SECTION_PATTERN = re.compile(r"(?m)^## v\d+\.\d+\.\d+ - \d{4}-\d{2}-\d{2}$")


def _version_key(tag: str) -> tuple[int, int, int]:
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ValueError(f"Invalid release tag: {tag}")
    return tuple(int(part) for part in match.groups())


def _version_tag(version: str) -> str:
    tag = version if version.startswith("v") else f"v{version}"
    _version_key(tag)
    return tag


def validate_bump(value: str) -> str:
    if value not in BUMP_TYPES:
        allowed = ", ".join(sorted(BUMP_TYPES))
        raise ValueError(f"Release bump must be one of {allowed}, got {value!r}")
    return value


def release_directive(body: str) -> str:
    """Parse the machine-readable release directive from a PR body."""
    matches = DIRECTIVE_PATTERN.findall(body)
    if not matches:
        if DIRECTIVE_MARKER_PATTERN.search(body):
            raise ValueError("Malformed release directive")
        return "patch"
    directives = {validate_bump(value) for value in matches}
    if len(directives) != 1:
        raise ValueError(
            "Conflicting release directives: " + ", ".join(sorted(directives))
        )
    return matches[0]


def validate_pull_request(body: str) -> str:
    return release_directive(body)


def bump_version(version: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    validate_bump(bump)
    major, minor, patch = version
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def next_version_from_tags(tags: Iterable[str], bump: str = "patch") -> str:
    validate_bump(bump)
    if bump == "none":
        raise ValueError("A release version cannot be calculated for release:none")
    versions = [_version_key(tag) for tag in tags if TAG_PATTERN.fullmatch(tag)]
    current = max(versions, default=(0, 0, 0))
    return ".".join(str(part) for part in bump_version(current, bump))


def generated_versions(changelog: str) -> list[str]:
    generated_match = re.search(
        rf"(?s){re.escape(GENERATED_START)}(.*?){re.escape(GENERATED_END)}",
        changelog,
    )
    if generated_match is None:
        return []
    return re.findall(
        r"(?m)^## (v\d+\.\d+\.\d+)(?: - \d{4}-\d{2}-\d{2})?$", generated_match.group(1)
    )


def changelog_introduces_version(parent: str, current: str, version: str) -> bool:
    """Check whether a particular generated heading first appears in a commit."""
    tag = _version_tag(version)
    return tag in set(generated_versions(current)) - set(generated_versions(parent))


def introduced_release_version(
    parent: str,
    current: str,
    published_tags: Iterable[str] = (),
    associated_release_tags: Iterable[str] = (),
    conflicting_published_tags: Iterable[str] = (),
) -> str | None:
    """Resolve a commit's release tag first, else apply the published-backfill filter."""
    introduced = set(generated_versions(current)) - set(generated_versions(parent))
    associated_tag_values = tuple(associated_release_tags)
    conflicts = introduced & (set(conflicting_published_tags) - set(associated_tag_values))
    if conflicts:
        raise ValueError(
            "Published release tags for introduced versions point to another source "
            "commit: " + ", ".join(sorted(conflicts, key=_version_key))
        )
    associated = {
        _version_tag(tag)
        for tag in associated_tag_values
        if TAG_PATTERN.fullmatch(tag if tag.startswith("v") else f"v{tag}")
    }
    matching_associations = introduced & associated
    if associated and associated != matching_associations:
        unexpected = sorted(associated - introduced, key=_version_key)
        raise ValueError(
            "Release tags on this source commit do not match its introduced changelog "
            "versions: " + ", ".join(unexpected)
        )
    if len(matching_associations) > 1:
        raise ValueError(
            "A source commit has multiple release tags for introduced versions: "
            + ", ".join(sorted(matching_associations, key=_version_key))
        )
    if matching_associations:
        return next(iter(matching_associations))

    published = set(published_tags)
    introduced = introduced - published
    introduced = sorted(introduced, key=_version_key)
    if len(introduced) > 1:
        raise ValueError(
            "A master commit introduced multiple generated release versions: "
            + ", ".join(introduced)
        )
    return introduced[0] if introduced else None


def validate_tag_target(tag_commit: str, target_commit: str, version: str) -> None:
    """Reject an existing release tag that does not identify its source commit."""
    if tag_commit != target_commit:
        raise ValueError(
            f"Release tag v{version} points to {tag_commit}, expected {target_commit}"
        )


def staging_update_needed(
    target_is_current_master: bool, source_digest: str, staging_digest: str
) -> bool:
    """Update staging only for current master when its immutable image differs."""
    return target_is_current_master and (
        not source_digest or source_digest != staging_digest
    )


def next_version_from_state(
    tags: Iterable[str], changelog: str, bump: str = "patch"
) -> str:
    return next_version_from_tags(
        [*tags, *generated_versions(changelog)],
        bump,
    )


def repository_tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def next_version(bump: str = "patch") -> str:
    return next_version_from_state(
        repository_tags(),
        (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
        bump,
    )


def latest_status_states(statuses: Iterable[Mapping[str, str]]) -> dict[str, str]:
    """Keep only the newest legacy commit status for each context."""
    latest: dict[str, tuple[str, int, str]] = {}
    for index, status in enumerate(statuses):
        context = status["context"]
        timestamp = status.get("updated_at") or status.get("created_at") or ""
        candidate = (timestamp, index, status["state"])
        if context not in latest or candidate[:2] > latest[context][:2]:
            latest[context] = candidate
    return {context: candidate[2] for context, candidate in latest.items()}


def _render_section(tag: str, title: str, author: str, number: str, url: str) -> str:
    clean_title = " ".join(title.split())
    if not clean_title:
        raise ValueError("A release PR must have a non-empty title")
    return f"## {tag}\n\n- {clean_title} by @{author} in {url or f'pull/{number}'}"


def update_changelog(
    existing: str, version: str, title: str, author: str, number: str, url: str
) -> str:
    """Add or replace one undated generated release while retaining legacy history."""
    tag = _version_tag(version)
    generated_match = re.search(
        rf"(?s){re.escape(GENERATED_START)}\n?(.*?){re.escape(GENERATED_END)}",
        existing,
    )
    if generated_match:
        prefix = existing[: generated_match.start()]
        generated_body = generated_match.group(1)
        legacy = existing[generated_match.end() :].lstrip("\n")
    else:
        first_legacy = LEGACY_SECTION_PATTERN.search(existing)
        split_at = first_legacy.start() if first_legacy else len(existing)
        prefix = existing[:split_at].rstrip()
        generated_body = ""
        legacy = existing[split_at:].lstrip("\n")

    sections = {
        section_tag: body.strip()
        for section_tag, body in GENERATED_SECTION_PATTERN.findall(generated_body)
    }
    sections[tag] = _render_section(tag, title, author, number, url).split("\n", 2)[2]
    rendered = []
    for section_tag in sorted(sections, key=_version_key, reverse=True):
        rendered.append(f"## {section_tag}\n\n{sections[section_tag]}")
    rendered_sections = "\n\n".join(rendered)
    generated = f"{GENERATED_START}\n\n{rendered_sections}\n\n{GENERATED_END}"
    if not prefix:
        prefix = "# Changelog"
    return f"{prefix.rstrip()}\n\n{generated}\n\n{legacy.rstrip()}\n"


def changelog_version(existing: str, tags: Iterable[str]) -> str | None:
    """Return the highest generated version that has not been tagged yet."""
    generated_match = re.search(
        rf"(?s){re.escape(GENERATED_START)}(.*?){re.escape(GENERATED_END)}", existing
    )
    if generated_match is None:
        return None
    tagged = set(tags)
    candidates = [
        tag
        for tag in re.findall(r"(?m)^## (v\d+\.\d+\.\d+)$", generated_match.group(1))
        if tag not in tagged
    ]
    return max(candidates, key=_version_key) if candidates else None


def changelog_entry(existing: str, version: str) -> str:
    tag = _version_tag(version)
    generated_match = re.search(
        rf"(?s){re.escape(GENERATED_START)}(.*?){re.escape(GENERATED_END)}", existing
    )
    if generated_match is None:
        raise ValueError(f"No generated changelog entry for {tag}")
    for section_tag, body in GENERATED_SECTION_PATTERN.findall(
        generated_match.group(1)
    ):
        if section_tag == tag:
            return f"## {tag}\n\n{body.strip()}"
    raise ValueError(f"No generated changelog entry for {tag}")


def _write_changelog(path: Path, args: argparse.Namespace) -> None:
    path.write_text(
        update_changelog(
            path.read_text(encoding="utf-8"),
            args.version,
            args.title,
            args.author,
            args.number,
            args.url,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    directive_parser = subparsers.add_parser("directive")
    directive_parser.add_argument("body", nargs="?")
    next_parser = subparsers.add_parser("next-version")
    next_parser.add_argument("bump", nargs="?", default="patch")
    changelog_parser = subparsers.add_parser("prepare-changelog")
    changelog_parser.add_argument("path", type=Path)
    changelog_parser.add_argument("version")
    changelog_parser.add_argument("title")
    changelog_parser.add_argument("author")
    changelog_parser.add_argument("number")
    changelog_parser.add_argument("url")
    version_parser = subparsers.add_parser("changelog-version")
    version_parser.add_argument("path", type=Path)
    entry_parser = subparsers.add_parser("changelog-entry")
    entry_parser.add_argument("path", type=Path)
    entry_parser.add_argument("version")
    delta_parser = subparsers.add_parser("changelog-delta")
    delta_parser.add_argument("parent", type=Path)
    delta_parser.add_argument("current", type=Path)
    delta_parser.add_argument("--published-tag", action="append", default=[])
    delta_parser.add_argument("--associated-tag", action="append", default=[])
    delta_parser.add_argument("--conflicting-tag", action="append", default=[])
    introduced_parser = subparsers.add_parser("changelog-introduces")
    introduced_parser.add_argument("parent", type=Path)
    introduced_parser.add_argument("current", type=Path)
    introduced_parser.add_argument("version")
    tag_parser = subparsers.add_parser("validate-tag-target")
    tag_parser.add_argument("tag_commit")
    tag_parser.add_argument("target_commit")
    tag_parser.add_argument("version")
    staging_parser = subparsers.add_parser("staging-needed")
    staging_parser.add_argument("target_is_current_master", choices=("true", "false"))
    staging_parser.add_argument("source_digest")
    staging_parser.add_argument("staging_digest")
    validate_parser = subparsers.add_parser("validate-pr")
    validate_parser.add_argument("event", type=Path)
    args = parser.parse_args()

    if args.command == "directive":
        print(
            release_directive(args.body if args.body is not None else sys.stdin.read())
        )
    elif args.command == "next-version":
        print(next_version(args.bump))
    elif args.command == "prepare-changelog":
        _write_changelog(args.path, args)
    elif args.command == "changelog-version":
        version = changelog_version(
            args.path.read_text(encoding="utf-8"), repository_tags()
        )
        if version:
            print(version.removeprefix("v"))
    elif args.command == "changelog-entry":
        print(changelog_entry(args.path.read_text(encoding="utf-8"), args.version))
    elif args.command == "changelog-delta":
        version = introduced_release_version(
            args.parent.read_text(encoding="utf-8"),
            args.current.read_text(encoding="utf-8"),
            args.published_tag,
            args.associated_tag,
            args.conflicting_tag,
        )
        if version:
            print(version.removeprefix("v"))
    elif args.command == "changelog-introduces":
        print(
            str(
                changelog_introduces_version(
                    args.parent.read_text(encoding="utf-8"),
                    args.current.read_text(encoding="utf-8"),
                    args.version,
                )
            ).lower()
        )
    elif args.command == "validate-tag-target":
        validate_tag_target(args.tag_commit, args.target_commit, args.version)
    elif args.command == "staging-needed":
        print(
            str(
                staging_update_needed(
                    args.target_is_current_master == "true",
                    args.source_digest,
                    args.staging_digest,
                )
            ).lower()
        )
    else:
        import json

        event = json.loads(args.event.read_text(encoding="utf-8"))
        print(
            f"Pull request release directive: {validate_pull_request(event['pull_request'].get('body') or '')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
