---
name: code-hygiene
description: >-
  Use for non-trivial code edits, refactors, reviews, tests, and implementation cleanup where local style choices affect maintainability. Apply dojo's code hygiene preferences: semantic contextual comments, simplicity over speculative abstraction, duplicated decisions over coincidental repetition, boolean clarity, structural control-flow review, readable names, and deterministic checks first. Do not use for typo-only fixes or purely mechanical formatting.
---

# Code Hygiene

Use this skill when changing implementation details, reviewing code, adding tests, or cleaning up non-trivial local complexity.

## Operating Rules

1. Prefer the smallest correct change.
2. Run deterministic checks before relying on agent judgment when a rule can be enforced mechanically. Use the root `justfile` entrypoints when they exist: `just lint-api` for Ruff/FBT, `just lint-web` for frontend lint, `just format-check` for formatting, and the narrowest relevant test recipe for behavior.
3. Remove duplicated decisions, not coincidental syntax.
4. Prefer comments that explain why, not what.
5. Treat long uncommented code as a review smell, not a comment quota.
6. Avoid new helpers, options, flags, abstractions, or compatibility paths until there is concrete pressure.

## Progressive Disclosure

Read only the reference files that match the edit:

- `references/python.md`: Python examples, Ruff FBT implications, naming, comments.
- `references/typescript-vue.md`: TypeScript/Vue examples, props, composables, component hygiene.
- `references/shared-examples.md`: language-agnostic do/don't examples.

## Comments

A comment that restates the line above it is dead weight. The code already says what; a comment earns its place by saying why, especially when the why is not recoverable from code itself: an external constraint, a tradeoff, an invariant, or a "don't touch this or X breaks" warning.

Large swaths of uncommented non-trivial code are a red flag. Ask whether names, types, tests, and structure are enough to recover intent. If not, add one concise contextual comment at the decision boundary, invariant, external constraint, or surprising tradeoff.

Do not add comments simply to break up visual space.

## Simplicity

Avoid speculative abstraction. Keep code in one function unless a helper has a real independent concept, reuse pressure, or a testability benefit.

Do not add backward-compatibility code unless there is persisted data, shipped behavior, external consumers, or an explicit requirement.

## Duplication

Not all similar-looking code is duplication worth removing. Two functions that both loop over a list are not duplicated logic by default.

What matters is duplicated decisions: the same business rule, invariant, query shape, API contract, conversion, or branching decision expressed in multiple places where it can drift.

## Boolean Clarity

Boolean blindness is a readability problem. Named booleans can be acceptable, but positional booleans and ambiguous flags should trigger review. Prefer explicit modes, enums, discriminated unions, or named functions when a boolean hides intent.

Two adjacent booleans are worse than one: callers can silently swap them and the type checker will accept both orders. If the combination space is not meaningful, split the operation into named functions or use a value that names its own state.

## Structural Control Flow

Actively look for places where branching on shape, variant, enum, command, or tagged state would be clearer as pattern matching, a discriminated union, or a lookup table.

Do not turn simple guards or two-way conditionals into clever structures just for style.

## Tests

Test behavior and invariants rather than private helper structure. A cleanup that preserves behavior should not force tests to know about incidental decomposition.
