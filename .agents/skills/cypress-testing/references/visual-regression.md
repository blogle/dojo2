# Cypress visual regression -- fixture-scoped, deterministic, and narrow

Loaded from the `cypress-testing` skill when setting up or debugging component
snapshots.

## Scope

Visual checks should stay narrow:

- shared component scenarios mounted from their fixture files
- deterministic rendering environments
- no permanent page-vs-mock screenshot gate

The bootstrap screenshot comparison for `/dev/design-system` is a temporary
agent-driven review process, not the ongoing CI model.

## Determinism checklist

1. Disable animations during snapshot runs.
2. Use a fixed viewport.
3. Wait for fonts before snapshotting.
4. Use fixed dates and fixed data.
5. Stub network calls.
6. Keep the baseline environment pinned in CI.

## Practical stance

If a snapshot does not help humans reason about a component's visual states,
skip it. Structural assertions and behavior tests are usually more valuable for
page shell code than broad full-page image diffs.
