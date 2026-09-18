#!/usr/bin/env python3
"""Calculate release versions from commit-title directives."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
RELEASE_DIRECTIVE_PATTERN = re.compile(r"\[release:([^\]\s]+)\]")
BUMP_TYPES = frozenset({"patch", "minor", "major", "none"})


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
    args = parser.parse_args()

    if args.command == "next-version":
        print(next_version(args.bump))
    else:
        title = args.title if args.title is not None else sys.stdin.read()
        print(release_directive(title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
