#!/usr/bin/env python3
"""Prepare a tagged dojo release from the repository's Unreleased notes."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
RELEASE_COMMENT = "<!-- Release automation promotes these notes to the next patch version on master. -->"


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


def next_version() -> str:
    versions = repository_tags()
    if not versions:
        return "0.0.1"
    major, minor, patch = max(versions)
    return f"{major}.{minor}.{patch + 1}"


def validate_version(value: str) -> str:
    if VERSION_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Release version must be MAJOR.MINOR.PATCH, got {value!r}")
    return value


def has_release_notes(body: str) -> bool:
    without_comments = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    return bool(without_comments.strip())


def replace_first_version(path: Path, pattern: re.Pattern[str], version: str) -> None:
    content = path.read_text(encoding="utf-8")
    updated, replacements = pattern.subn(rf'\g<prefix>"{version}"', content, count=1)
    if replacements != 1:
        raise ValueError(f"Could not find the package version in {path}")
    path.write_text(updated, encoding="utf-8")


def promote(version: str, release_date: str) -> bool:
    validate_version(version)
    date.fromisoformat(release_date)

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    # Keep the automation marker scoped to Unreleased rather than copying it
    # into every historical version section.
    changelog = re.sub(
        rf"(?m)^(## v\d+\.\d+\.\d+[^\n]*)\n\n{re.escape(RELEASE_COMMENT)}\n",
        r"\1\n",
        changelog,
    )
    unreleased = re.search(r"(?m)^## Unreleased\s*$", changelog)
    if unreleased is None:
        raise ValueError("CHANGELOG.md must contain an Unreleased section")
    next_heading = re.search(r"(?m)^##\s+", changelog[unreleased.end() :])
    body_end = unreleased.end() + (next_heading.start() if next_heading else len(changelog))
    body = changelog[unreleased.end() : body_end].strip()
    if not has_release_notes(body):
        print("No Unreleased notes; no release prepared.")
        return False
    if re.search(rf"(?m)^## v{re.escape(version)}\s+", changelog):
        raise ValueError(f"CHANGELOG.md already contains v{version}")

    suffix = changelog[body_end:] if next_heading else ""
    replacement = (
        "## Unreleased\n\n"
        f"{RELEASE_COMMENT}\n\n"
        f"## v{version} - {release_date}\n\n"
        f"{body}\n\n"
    )
    changelog_path.write_text(changelog[: unreleased.start()] + replacement + suffix, encoding="utf-8")

    replace_first_version(
        ROOT / "api/pyproject.toml",
        re.compile(r"(?m)^(?P<prefix>version\s*=\s*)\"[^\"]+\""),
        version,
    )
    replace_first_version(
        ROOT / "api/uv.lock",
        re.compile(r'(?ms)^(?P<prefix>name = "dojo-api"\nversion = )"[^"]+"'),
        version,
    )
    replace_first_version(
        ROOT / "web/package.json",
        re.compile(r'(?m)^(?P<prefix>\s*"version":\s*)"[^"]+"'),
        version,
    )
    print(f"Prepared v{version} release metadata for {release_date}.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("next-version")
    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("version")
    promote_parser.add_argument("release_date")
    args = parser.parse_args()

    if args.command == "next-version":
        print(next_version())
        return 0
    promote(args.version, args.release_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
