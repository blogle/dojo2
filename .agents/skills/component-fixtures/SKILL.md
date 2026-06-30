---
name: component-fixtures
description: Use whenever creating or updating a shared component under web/src/dojo/components/, wiring a component into the /dev/design-system page, or writing Cypress component tests. Defines the single colocated fixture-file contract consumed by both the catalog and Cypress.
---

# Component fixtures

Every shared component has exactly one colocated `<Name>.fixtures.ts` file.
It is the only place representative visual scenarios are defined.

- The design-system page imports it to render live states.
- Cypress component tests import the same file to mount the same scenarios.
- Do not define example props inline in either consumer.

## File location and naming

- `web/src/dojo/components/<area>/<Name>.vue`
- `web/src/dojo/components/<area>/<Name>.fixtures.ts`

The colocated naming is strict.

## Contract

The shared fixture type should live in:

- `web/src/dojo/components/fixtures.ts`

The fixture object should expose the component directly and be type-checked
against the component props.

Shape:

- `component`
- `title`
- `description`
- optional top-level `presentation`
- `scenarios`

Each scenario may include:

- `name`
- optional `description`
- optional `props`
- optional `slots`
- optional `notes`
- optional `presentation`

Use a top-level default `presentation` with optional per-scenario override.

## Presentation metadata

Fixtures stay portable. They do not own arbitrary wrapper markup.

Allow only a very small presentation hint surface when needed for responsive or
context-sensitive components, for example:

- `viewport`
- `container`

If a component needs a realistic host context, solve that with standardized
presentation hints or a shared harness, not bespoke catalog-only wrapper code.

## What belongs in fixtures

- Representative states worth seeing during design/development iteration
- Deterministic props and slots
- Scenarios that materially change layout, density, overflow, hierarchy, or tone

## What does not belong in fixtures

- Exhaustive behavior matrices
- Randomized or time-relative data
- App-specific page scaffolding
- Hidden logic that only one consumer knows how to interpret

If a state is important to behavior but not visually useful, put it in tests,
not fixtures.

## Determinism rules

- No `new Date()`
- No `Math.random()`
- No relative time labels
- No live network data

If the component needs dates or asynchronous data, fixtures must pin them to
literal stable values.
