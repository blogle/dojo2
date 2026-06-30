#!/usr/bin/env python3
"""
check_hardcoded_values.py

Fails (exit 1) if any hex color literal appears in web/ source outside the
generated token file. Warns (exit 0) on raw px values in spacing/radius-like
declarations, since not every px is a violation (for example a 1px border).

Usage:
    python3 .agents/skills/design-tokens/scripts/check_hardcoded_values.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_SRC = REPO_ROOT / "web" / "src"

ALLOWLIST = {
    WEB_SRC / "dojo" / "design-system" / "tokens.css",
}

HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{2})?\b")
IGNORE_MARKER_RE = re.compile(r"token-lint-ignore:\s*\S")
SPACING_PROP_RE = re.compile(
    r"(?:margin|padding|gap|row-gap|column-gap|border-radius)[^:;{}]*:\s*[^;]*?(\d+)px"
)

SCAN_GLOBS = ("**/*.vue", "**/*.ts", "**/*.css")


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


def check_file(path: Path):
    errors, warnings = [], []
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in HEX_COLOR_RE.finditer(line):
            if IGNORE_MARKER_RE.search(line):
                continue
            errors.append((lineno, line.strip(), match.group(0)))
        for match in SPACING_PROP_RE.finditer(line):
            if IGNORE_MARKER_RE.search(line):
                continue
            warnings.append((lineno, line.strip(), match.group(1)))
    return errors, warnings


def main():
    total_errors = 0
    total_warnings = 0
    for path in iter_source_files():
        if path.resolve() in ALLOWLIST:
            continue
        errors, warnings = check_file(path)
        rel = path.relative_to(REPO_ROOT)
        for lineno, line, match in errors:
            print(f"ERROR  {rel}:{lineno}  hardcoded color {match!r}\n         {line}")
            total_errors += 1
        for lineno, line, match in warnings:
            print(f"WARN   {rel}:{lineno}  raw spacing value (~{match}px)\n         {line}")
            total_warnings += 1

    print(f"\n{total_errors} hardcoded-color error(s), {total_warnings} raw-spacing warning(s).")
    if total_errors:
        print("Promote the value into DESIGN.md front matter, regenerate tokens.css, and reference var(--*).")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
