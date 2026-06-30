---
name: cypress-testing
description: Use whenever writing, running, or debugging Cypress tests under web/, especially shared component tests, fixture-driven snapshots, or visual regressions. Covers the fixture-driven component-testing workflow and the narrow role of visual snapshots after bootstrap.
---

# Cypress testing

Two reference docs live with this skill:

- `references/component-testing.md`
- `references/visual-regression.md`

Both assume the `component-fixtures` convention: tests consume the colocated
fixture object and iterate over its representative scenarios rather than
re-describing example props inline.

## Firm choices

- Cypress component tests mount shared components through `cypress/vue`.
- Shared components should expose stable `data-cy` hooks for interactive
  elements.
- Component snapshots, when used, are fixture-driven and deterministic.
- Do not turn the bootstrap screenshot mock into a permanent full-page visual
  diff gate.

Use component-level visual checks where they are valuable; keep page-shell
confidence primarily structural.
