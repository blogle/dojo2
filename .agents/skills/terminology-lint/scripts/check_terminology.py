#!/usr/bin/env python3
"""
check_terminology.py

Fails (exit 1) if any banned phrase from terms.yaml appears anywhere in web/src
using a case-insensitive substring match.

Usage:
    python3 .agents/skills/terminology-lint/scripts/check_terminology.py
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_SRC = REPO_ROOT / "web" / "src"
TERMS_PATH = Path(__file__).resolve().parent / "terms.yaml"

SCAN_GLOBS = ("**/*.vue", "**/*.ts")


def iter_source_files():
    if not WEB_SRC.exists():
        return
    seen = set()
    for pattern in SCAN_GLOBS:
        for path in WEB_SRC.glob(pattern):
            if path in seen or "node_modules" in path.parts:
                continue
            seen.add(path)
            yield path


def main():
    terms = yaml.safe_load(TERMS_PATH.read_text(encoding="utf-8")) or {}
    banned = terms.get("banned_phrases") or []
    if not banned:
        print("terms.yaml has no banned_phrases -- nothing to check.")
        sys.exit(0)

    total_hits = 0
    for path in iter_source_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        rel = path.relative_to(REPO_ROOT)
        for entry in banned:
            phrase = entry["phrase"].lower()
            if phrase not in lower:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if phrase in line.lower():
                    print(f"ERROR  {rel}:{lineno}  banned phrase {entry['phrase']!r}")
                    print(f"         {line.strip()}")
                    print(f"         why: {entry['reason'].strip()}")
                    total_hits += 1

    print(f"\n{total_hits} banned-phrase hit(s) across {len(banned)} rule(s).")
    sys.exit(1 if total_hits else 0)


if __name__ == "__main__":
    main()
