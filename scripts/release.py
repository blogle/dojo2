#!/usr/bin/env python3
"""Calculate release versions from commit-title directives."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
RELEASE_DIRECTIVE_PATTERN = re.compile(r"\[release:([^\]\s]+)\]")
BUMP_TYPES = frozenset({"patch", "minor", "major", "none"})
RELEASE_SECTION_PATTERN = re.compile(r"(?m)^## (v\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}$")


class ReleaseRecord(TypedDict):
    tag: str
    date: str
    body: str | Sequence[str]


def _version_key(tag: str) -> tuple[int, int, int]:
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ValueError(f"Invalid release tag: {tag}")
    return tuple(int(part) for part in match.groups())


def _release_bullets(body: str | Sequence[str]) -> list[str]:
    if not isinstance(body, str):
        return [f"- {bullet.removeprefix('- ').removeprefix('* ')}" for bullet in body]
    bullets = [
        line.strip()[2:]
        for line in body.splitlines()
        if line.strip().startswith(("- ", "* "))
    ]
    return [f"- {bullet}" for bullet in bullets if bullet and "Full Changelog" not in bullet]


def changelog_versions(changelog: str) -> set[str]:
    return set(RELEASE_SECTION_PATTERN.findall(changelog))


def validate_changelog(changelog: str, releases: Sequence[ReleaseRecord]) -> None:
    missing = sorted(
        {release["tag"] for release in releases} - changelog_versions(changelog),
        key=_version_key,
    )
    if missing:
        raise ValueError("Changelog is missing published releases: " + ", ".join(missing))


def sync_changelog(existing: str, releases: Sequence[ReleaseRecord]) -> str:
    """Add published release records without changing existing release history."""
    existing_tags = changelog_versions(existing)
    sections: list[str] = []
    for release in releases:
        tag = release["tag"]
        _version_key(tag)
        if tag in existing_tags:
            continue
        date = release["date"]
        bullets = _release_bullets(release["body"])
        sections.append(f"## {tag} - {date}\n\n" + "\n".join(bullets))
    if not sections:
        validate_changelog(existing, releases)
        return existing
    sections.sort(
        key=lambda section: _version_key(section.split()[1]),
        reverse=True,
    )
    insertion = "\n\n".join(sections)
    first_release = re.search(r"(?m)^## v\d+\.\d+\.\d+ - \d{4}-\d{2}-\d{2}$", existing)
    history = existing[first_release.start() :] if first_release else ""
    prefix = existing[: first_release.start()] if first_release else existing.rstrip() + "\n\n"
    result = prefix + insertion + ("\n\n" if insertion else "") + history
    validate_changelog(result, releases)
    return result


def _sync_changelog_file(path: Path) -> None:
    releases: list[ReleaseRecord] = json.load(sys.stdin)
    path.write_text(sync_changelog(path.read_text(encoding="utf-8"), releases), encoding="utf-8")


def repository_tags() -> list[tuple[int, int, int]]:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    versions = []
    for tag in result.stdout.splitlines():
        match = TAG_PATTERN.fullmatch(tag)
        if match is not None:
            versions.append(tuple(int(part) for part in match.groups()))
    return versions


def validate_bump(value: str) -> str:
    if value not in BUMP_TYPES:
        allowed = ", ".join(sorted(BUMP_TYPES))
        raise ValueError(f"Release bump must be one of {allowed}, got {value!r}")
    return value


def release_directive(title: str) -> str:
    """Return the release directive encoded in a commit title."""
    first_line = title.splitlines()[0] if title else ""
    matches = RELEASE_DIRECTIVE_PATTERN.findall(first_line)
    if not matches:
        if "[release:" in first_line:
            raise ValueError("Malformed release directive")
        return "patch"
    invalid = sorted(set(matches) - BUMP_TYPES)
    if invalid:
        raise ValueError(f"Unknown release directive: {invalid[0]!r}")
    directives = set(matches)
    if len(directives) > 1:
        raise ValueError(
            "Conflicting release directives: " + ", ".join(sorted(directives))
        )
    return matches[0]


def bump_version(version: tuple[int, int, int], bump: str) -> tuple[int, int, int]:
    validate_bump(bump)
    major, minor, patch = version
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def next_version(bump: str = "patch") -> str:
    validate_bump(bump)
    if bump == "none":
        raise ValueError("A release version cannot be calculated for release:none")
    versions = repository_tags()
    if not versions:
        major, minor, patch = 0, 0, 0
    else:
        major, minor, patch = max(versions)
    major, minor, patch = bump_version((major, minor, patch), bump)
    return f"{major}.{minor}.{patch}"


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    next_parser = subparsers.add_parser("next-version")
    next_parser.add_argument("bump", nargs="?", default="patch")
    directive_parser = subparsers.add_parser("directive")
    directive_parser.add_argument("title", nargs="?")
    sync_parser = subparsers.add_parser("sync-changelog")
    sync_parser.add_argument("path", type=Path)
    args = parser.parse_args()

    if args.command == "next-version":
        print(next_version(args.bump))
    elif args.command == "directive":
        title = args.title if args.title is not None else sys.stdin.read()
        print(release_directive(title))
    else:
        _sync_changelog_file(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
