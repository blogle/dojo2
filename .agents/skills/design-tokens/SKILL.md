---
name: design-tokens
description: Use whenever writing or reviewing CSS, Tailwind theme values, inline style props, DESIGN.md front matter, or web/src/dojo/design-system/tokens.css. Also use before running frontend checks after styling changes. Enforces DESIGN.md as the canonical token source and tokens.css as the only generated runtime token artifact.
---

# Design tokens

`DESIGN.md` front matter is the canonical source of design tokens. The
generator reads the YAML front matter only and writes
`web/src/dojo/design-system/tokens.css`.

Do not treat any of the following as canonical:

- prose in the Markdown body of `DESIGN.md`
- screenshots
- Tailwind config literals
- hardcoded values in components

## Current contract

- Required token families live in `DESIGN.md` front matter.
- `tokens.css` is generated, committed, and consumed across the app.
- Tailwind should reference CSS variables, not restate literal values.
- If a design nuance matters repeatedly, promote it into `DESIGN.md` and
  regenerate `tokens.css`.

## Before writing any style

1. Open `tokens.css` and reuse an existing variable.
2. If the value expresses durable design taste and no token exists, add it to
   `DESIGN.md` front matter and regenerate.
3. Do not introduce a literal hex, px spacing value, radius, shadow, or other
   token-like value as a shortcut.

## Naming

Prefer plain semantic family prefixes:

- `--color-*`
- `--space-*`
- `--radius-*`
- `--text-*`
- `--layout-*`
- `--shadow-*`
- `--transition-*`

Avoid project prefixes like `--dojo-*` unless a real external conflict makes
them necessary.

## Bootstrap note

The screenshot mock is only a temporary bootstrap calibration reference.
During that phase it may be used to verify that `DESIGN.md` is encoded
correctly. After alignment, retire the screenshot and continue with
`DESIGN.md -> tokens.css` only.

During that calibration phase, the palette in the mock should agree exactly
with `DESIGN.md`. If there is disagreement, update `DESIGN.md` and regenerate
`tokens.css`; do not patch the generated file by hand.

## Commands

Expected workflow:

- explicit generation command in `just`, e.g. `just generate-design-tokens`
- root `just check` verifies `tokens.css` is current

Generator script:

```bash
python3 .agents/skills/design-tokens/scripts/generate_tokens.py
```

Hardcoded-value lint:

```bash
python3 .agents/skills/design-tokens/scripts/check_hardcoded_values.py
```

## Enforcement

`check_hardcoded_values.py` should fail on raw hex values outside `tokens.css`
and warn on suspicious raw spacing/radius values. Token policy belongs in CI,
not just in code review memory.
