#!/usr/bin/env python3
"""
generate_tokens.py

Generates web/src/dojo/design-system/tokens.css from DESIGN.md YAML front
matter.

The Markdown body is not parsed for token values. If a durable design value is
missing, add it to the front matter instead of hardcoding it elsewhere. During
bootstrap, if the mock PNG and generated tokens disagree, fix DESIGN.md and
regenerate; do not edit tokens.css directly.

Usage:
    python3 .agents/skills/design-tokens/scripts/generate_tokens.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DESIGN_MD = REPO_ROOT / "DESIGN.md"
TOKENS_CSS = REPO_ROOT / "web" / "src" / "dojo" / "design-system" / "tokens.css"

FAMILY_PREFIXES = {
    "colors": "color",
    "spacing": "space",
    "rounded": "radius",
    "typography": "text",
    "layout": "layout",
    "shadows": "shadow",
    "transitions": "transition",
}
REQUIRED_FAMILIES = ("colors", "spacing", "rounded", "typography")
TOKEN_REF_RE = re.compile(r"\{([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+)\}")


def load_front_matter() -> dict:
    text = DESIGN_MD.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit("DESIGN.md must start with YAML front matter")
    _, yaml_block, _ = text.split("---", 2)
    data = yaml.safe_load(yaml_block) or {}
    for family in REQUIRED_FAMILIES:
        if family not in data:
            raise SystemExit(f"DESIGN.md front matter missing required family: {family}")
    return data


def camel_to_kebab(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", value).replace("_", "-").lower()


def normalize_name(value: str) -> str:
    return camel_to_kebab(str(value))


def resolve_references(value: object) -> str:
    text = str(value)

    def replace(match: re.Match[str]) -> str:
        path = match.group(1)
        parts = path.split(".")
        family = FAMILY_PREFIXES.get(parts[0], normalize_name(parts[0]))
        rest = "-".join(normalize_name(part) for part in parts[1:])
        return f"var(--{family}-{rest})"

    return TOKEN_REF_RE.sub(replace, text)


def emit_family(prefix: str, value: object, path: list[str], lines: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            emit_family(prefix, child, path + [normalize_name(key)], lines)
        return

    token_name = "-".join(path)
    lines.append(f"  --{prefix}-{token_name}: {resolve_references(value)};")


def build_css(data: dict) -> str:
    lines = [
        "/* tokens.css",
        " * Generated from DESIGN.md front matter by generate_tokens.py.",
        " * Do not hand-edit; update DESIGN.md and regenerate. */",
        "",
        ":root {",
    ]

    for family, prefix in FAMILY_PREFIXES.items():
        family_data = data.get(family)
        if not isinstance(family_data, dict):
            continue
        lines.append(f"  /* {family} */")
        emit_family(prefix, family_data, [], lines)
        lines.append("")

    if lines[-1] == "":
        lines.pop()
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = load_front_matter()
    css = build_css(data)
    TOKENS_CSS.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_CSS.write_text(css, encoding="utf-8")
    print(f"Wrote {TOKENS_CSS.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
