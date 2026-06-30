#!/usr/bin/env python3
"""
check_manifest_coverage.py

Validates web/src/dojo/design-system/manifest.yaml against the agreed initial
schema and the fixture files present on disk.

Current contract:
  - top-level keys: page_shell, sections
  - section keys: id, title, entries, optional description
  - entry keys: component, fixture
  - only truthfully populated sections belong in the manifest

Usage:
    python3 .agents/skills/design-system/scripts/check_manifest_coverage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DESIGN_SYSTEM_DIR = REPO_ROOT / "web" / "src" / "dojo" / "design-system"
COMPONENTS_DIR = REPO_ROOT / "web" / "src" / "dojo" / "components"
MANIFEST_PATH = DESIGN_SYSTEM_DIR / "manifest.yaml"

REQUIRED_PAGE_SHELL_KEYS = {
    "container_max_width",
    "quick_nav",
    "intro",
    "section_heading_format",
    "section_gap",
}
REQUIRED_SECTION_KEYS = {"id", "title", "entries"}
REQUIRED_ENTRY_KEYS = {"component", "fixture"}

had_error = False


def fail(message: str) -> None:
    global had_error
    had_error = True
    print(f"ERROR  {message}")


def normalize_fixture_path(raw_path: str) -> Path:
    return COMPONENTS_DIR / raw_path


def main() -> None:
    if not MANIFEST_PATH.exists():
        fail(f"manifest not found at {MANIFEST_PATH.relative_to(REPO_ROOT)}")
        sys.exit(1)

    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}

    page_shell = manifest.get("page_shell")
    if not isinstance(page_shell, dict):
        fail("manifest has no page_shell mapping")
    else:
        missing = sorted(REQUIRED_PAGE_SHELL_KEYS - page_shell.keys())
        if missing:
            fail(f"page_shell missing keys: {missing}")
        intro = page_shell.get("intro") or {}
        intro_fixture = intro.get("fixture")
        if not intro_fixture:
            fail("page_shell.intro.fixture is required")
        else:
            intro_path = normalize_fixture_path(intro_fixture)
            if not intro_path.exists():
                fail(
                    "page_shell.intro fixture not found at "
                    f"web/src/dojo/components/{intro_fixture}"
                )

    sections = manifest.get("sections")
    if not isinstance(sections, list) or not sections:
        fail("manifest must declare at least one populated section")
        sys.exit(1)

    seen_section_ids: set[str] = set()
    seen_fixture_paths: set[Path] = set()
    seen_components: set[str] = set()

    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            fail(f"section #{index} is not a mapping")
            continue

        missing = sorted(REQUIRED_SECTION_KEYS - section.keys())
        sid = section.get("id", f"<section-{index}>")
        if missing:
            fail(f"section '{sid}' missing keys: {missing}")
            continue

        if sid in seen_section_ids:
            fail(f"duplicate section id: {sid}")
        seen_section_ids.add(sid)

        entries = section.get("entries")
        if not isinstance(entries, list) or not entries:
            fail(f"section '{sid}' must have at least one entry")
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                fail(f"section '{sid}' has a non-mapping entry: {entry!r}")
                continue

            missing_entry_keys = sorted(REQUIRED_ENTRY_KEYS - entry.keys())
            if missing_entry_keys:
                fail(f"section '{sid}' entry missing keys: {missing_entry_keys}")
                continue

            component = entry["component"]
            fixture_rel = entry["fixture"]
            fixture_path = normalize_fixture_path(fixture_rel)

            if fixture_path in seen_fixture_paths:
                fail(f"fixture path reused across entries: {fixture_rel}")
            seen_fixture_paths.add(fixture_path)

            if component in seen_components:
                fail(f"component listed more than once in manifest: {component}")
            seen_components.add(component)

            if not fixture_path.exists():
                fail(
                    f"section '{sid}' / component '{component}': fixture not found at "
                    f"web/src/dojo/components/{fixture_rel}"
                )

    if had_error:
        sys.exit(1)

    print(
        f"OK -- {len(sections)} sections, {len(seen_components)} entries, all fixtures present."
    )


if __name__ == "__main__":
    main()
