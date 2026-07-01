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

## Catalog entry criteria

Before adding a component to `manifest.yaml`, evaluate whether it belongs in
the design system catalog. The catalog is for reusable design primitives and
complex bespoke components — not page-specific compositions of already-cataloged
atoms.

### Decision checklist

Run through these questions before adding an entry:

1. **Is it atomic and reused across multiple pages/screens?**
   If yes, it belongs in the catalog. These are the building blocks: `Button`,
   `TextField`, `Stack`, `Tabs`, etc.

2. **Does it have nontrivial internal logic, layout, or interaction that isn't
   just a stack of pre-existing atoms?**
   If yes, it belongs in the catalog even if it is page-specific. Nontrivial
   means custom state machines, complex responsive behavior, multi-step
   workflows, or interaction patterns that cannot be assembled from the
   existing atom set without significant glue code.

3. **Can it be fully described as "atom A + atom B + atom C" with no added
   behavior, state, or layout complexity beyond wrapping?**
   If yes, do not catalog it. It is a page-level composition, not a design
   primitive. The atoms it composes should speak for themselves on the catalog
   page.

### Include examples (belong in catalog)

- **`FormModal`** — Wraps a dialog with focus trapping, keyboard dismissal,
  form submission wiring, and validation error layout. The internal behavior
  (focus management, close-on-escape, submit-on-enter) is not trivially
  assembled from a generic dialog + a form.
- **`LargeDetailModal`** — Responsive full-height panel with header, scrollable
  body slots, footer, and tab slot. The layout contract and slot structure
  represent a reusable pattern beyond a simple dialog wrapper.
- **`HierarchicalCategoryTable`** — Tree-structured table with expand/collapse,
  indentation, and row-level actions. The hierarchical data handling and
  interaction model are not derivable from `TableShell` alone.

### Exclude examples (page-level compositions, not catalog entries)

- **`MoveFundsModal`** — Two `SelectField` dropdowns + one `CurrencyField` +
  a submit button inside `FormModal`. No tabs, no custom state, no layout
  complexity beyond vertical stacking. This is "atoms A + B + C."
- **`FundGroupModal`** — A dynamic-length list of `CurrencyField` inputs
  inside `FormModal` with a computed total. The aggregation logic is trivial
  (`parseFloat` + sum) and the layout is a flat grid. Compose it from
  `FormModal` + `CurrencyField` on the page.
- **`CategoryDetailModal`** — `LargeDetailModal` with a `Tabs` slot containing
  `KeyValueList` (overview), a stub (transactions), a read-only `GoalEditor`
  (goals), and another stub (funding). The tab-switching is just a `ref` keyed
  to `Tabs`; the content sections delegate to already-cataloged atoms.

### Rule of thumb

If a colleague can look at the catalog page and immediately understand the
component's visual and behavioral contract without seeing the source, it belongs
in the catalog. If it is just a wiring diagram of other catalog entries, it
does not.

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
