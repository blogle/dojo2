---
name: design-system
description: Use whenever working on DESIGN.md, web/src/dojo/design-system/, shared UI components under web/src/dojo/components/, fixtures, tokens.css generation, or the /dev/design-system route. This is the primary source of truth for the project design-system workflow, including token promotion, manifest rules, bootstrap visual alignment, and fixture conventions.
---

# Design system

This project's design system has one canonical source for design values:

- `DESIGN.md` front matter is gospel for tokens and durable design taste.
- `web/src/dojo/design-system/tokens.css` is a generated artifact.
- `web/src/dojo/design-system/manifest.yaml` is the structure spec for the
  `/dev/design-system` route.
- Shared components live under `web/src/dojo/components/` and each one ships
  exactly one colocated `<Name>.fixtures.ts` file.

Skills are workflow guidance and enforcement. They are not a competing source
of truth.

## Use this skill first

Load this skill before changing any of the following:

- `DESIGN.md`
- `web/src/dojo/design-system/manifest.yaml`
- `web/src/dojo/design-system/tokens.css`
- shared components in `web/src/dojo/components/`
- fixture files (`*.fixtures.ts`)
- `/dev/design-system` route code
- `just`/CI checks that enforce design-system rules

Then load the narrower supporting skills only as needed:

- `design-tokens`
- `component-fixtures`
- `cypress-testing`
- `terminology-lint`

## Source-of-truth hierarchy

1. `DESIGN.md` front matter defines tokens.
2. `tokens.css` is generated from `DESIGN.md`.
3. Tailwind and app/component styles consume generated CSS variables.
4. `manifest.yaml` defines the `/dev/design-system` page shell and the ordered,
   truthfully populated sections rendered on that route.
5. Component fixtures define representative visual scenarios for the catalog and
   Cypress component tests.

If the app appearance is wrong, the likely bug is one of:

- the `DESIGN.md -> tokens.css` translation layer
- component consumption of tokens
- catalog page shell/layout code

Do not paper over these with hardcoded literals or screenshot-derived guesses.

## `/dev/design-system` route rules

- The route is mounted in development only.
- The page navbar acts as a table of contents generated from
  `manifest.yaml` sections.
- Include only sections that have real content today.
- Initial truthful sections are expected to include `Foundations` and `Layout
  Primitives`.
- The page shell should preserve the mock's structure and design taste, but the
  long-term source of truth is `manifest.yaml` plus real components, not the
  screenshot.

## Manifest rules

`web/src/dojo/design-system/manifest.yaml` is hand-authored and canonical for
catalog structure.

Top-level keys:

- `page_shell`
- `sections`

Initial section shape:

- `id`
- `title`
- `entries`
- optional `description`

Initial entry shape:

- `component`
- `fixture`

Rules:

- Section titles store plain text like `Foundations`; numbering is added by the
  renderer from order.
- Include only populated sections.
- Every entry points to a real shared component and a real fixture file.
- Use token references in manifest values wherever the value expresses durable
  design taste.
- If a shell/layout nuance cannot be expressed cleanly, expand the token
  taxonomy in `DESIGN.md` rather than hardcoding it into the page.

## Shared component rules

- If a component lands in the design system, it is ready for real reuse.
- Do not create a shadow component library inside `design-system/`.
- Shared component names should be generic when truthful, domain-specific only
  when the behavior is truly domain-specific.
- Avoid project prefixes like `Dojo*` unless an actual external naming conflict
  requires one.
- Use PascalCase Vue component names.

Examples already aligned with the current docs include:

- `Stack`
- `Inline`
- `Grid`
- `Surface`
- `Divider`
- `NavigationRail`

The design-system page may use `NavigationRail` with table-of-contents entries;
the same shared component can be used elsewhere with route-oriented items.

## Fixture philosophy

Fixtures are for representative visual/design review states, not exhaustive
behavioral coverage.

- Add a fixture scenario when it is worth seeing.
- Do not turn fixtures into a permutation grid of every prop combination.
- Exhaustive behavior belongs in tests.

See the `component-fixtures` skill for the contract.

## Bootstrap visual alignment

During the initial bootstrap only, the screenshot mock is a temporary
calibration reference.

- Use it to align `DESIGN.md`, generated `tokens.css`, the page shell, and the
  foundations/layout rendering.
- The exact palette shown in the mock should exist in `DESIGN.md`. If the mock
  and `DESIGN.md` disagree during bootstrap, fix `DESIGN.md` and regenerate
  `tokens.css`.
- Do not convert that into a permanent screenshot-gate in CI.
- Use agent-driven screenshot review with a semantic rubric, not raw pixel diff.

Semantic review order:

1. Page structure
2. Section order and headings
3. Nav rail placement and TOC linkage
4. Container width and single-column rhythm
5. Foundations composition
6. Typography hierarchy and specimen ordering
7. Palette fidelity and swatch ordering
8. Spacing/radius presentation
9. Overall visual tone

Escalate to a human only when confidence is already high or the remaining
differences are subjective.

Retire the screenshot completely once all of the following are true:

- `DESIGN.md` has been calibrated against it
- `tokens.css` is generated and in use
- `/dev/design-system` is strikingly visually similar in structure and tone
- the bootstrap visual review is high confidence
- the ongoing lint/test/Cypress enforcement path is in place

After that point, remove the PNG and stop making decisions based on it.

## Enforcement expectations

The design system should be wired into normal repo checks, not treated as a
sidecar discipline.

Expected commands:

- explicit generation command for tokens
- `just check-design-system` for fast local iteration
- root `just check` includes design-system validation and CI relies on it

The supporting skills define the narrower checks. When design-system rules and
older bootstrap content disagree, follow this skill.
