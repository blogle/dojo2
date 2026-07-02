---
name: architecture-principles
description: >-
  Use for non-trivial code edits, refactors, reviews, new modules, API/model changes, tests, and domain logic changes. Apply dojo's architecture preferences: strict functional core with imperative shell unless explicitly justified, parse-don't-validate boundaries, typed domain representations over string-programming, explicit control-flow structure, single-responsibility boundaries, and durable tradeoff documentation. Do not use for typo-only fixes or purely mechanical formatting.
---

# Architecture Principles

Use this skill when a change affects boundaries, domain logic, data flow, API/model shape, persistence behavior, or tests that encode architectural decisions.

## Operating Rules

1. Prefer deterministic checks over judgment. Use the root `justfile` entrypoints when they exist: `just lint-api` for Ruff/FBT, `just architecture-check` for repository policy checks, `just format-check` for formatting, and the narrowest relevant test recipe for behavior.
2. Keep I/O, clocks, framework glue, database access, mutation, and UI events at the shell.
3. Keep calculations, transformations, parsing results, and business rules in a functional core.
4. Treat exceptions to functional core / imperative shell as design decisions. Make the justification explicit in code or docs when it is durable.
5. Parse raw input at boundaries into domain-shaped values. Do not repeatedly validate raw strings, dicts, nullable primitives, or sentinel values inside core logic.
6. Avoid string-programming. Do not dispatch, branch, or encode hidden modes in raw strings after the boundary.
7. Split code by responsibility, not by line count.

## Progressive Disclosure

Read only the reference files that match the edit:

- `references/python.md`: Python, FastAPI, Pydantic, Ruff FBT, dataclasses, `match`.
- `references/typescript-vue.md`: TypeScript, Vue, discriminated unions, props/events, composables.
- `references/shared-examples.md`: language-agnostic do/don't examples.

## Functional Core, Imperative Shell

Use a strict default: pure/domain code belongs in the core; effects belong at the edge. If extracting a pure core would make the code harder to understand, keep the simpler shape only with an explicit reason.

The shell talks to the outside world: DuckDB connections, HTTP requests, the wall clock, files, env vars, browser APIs, and Google Sheets. The core makes decisions: given data, what is the answer? This is why `clock.py` exists: a function that calls the wall clock internally cannot be tested deterministically, but a function that receives `now` can.

Good boundaries usually look like this:

- shell: read request, query database, call clock, mutate store, handle framework lifecycle
- core: parse accepted inputs, calculate balances, classify transactions, transform rows, decide statuses
- shell: persist, render, return HTTP response, emit event

## Parse, Don't Validate

Validate and parse at external boundaries, then pass typed/domain values inward. A value accepted by a parser should carry its invariant in the type or name.

Avoid inner code that repeatedly asks whether a supposedly accepted value is really valid. That is usually a sign that parsing happened too late or the domain type is too weak.

A boolean validity function throws away the work it just did. Prefer returning the parsed value or an explicit domain error when callers need to recover.

## Avoid String-Programming

Raw strings are appropriate at boundaries, storage, protocols, and user-facing copy. They are a poor representation for domain decisions.

Prefer enums, literal unions, discriminated unions, typed IDs, small value objects, or explicit lookup tables for modes, commands, statuses, field names, and dispatch keys.

## Structural Control Flow

Actively look for branching that is really about shape, variant, enum, command, or tagged state. Prefer `match`, discriminated unions, or lookup tables when they clarify the structure.

Do not rewrite simple guards, two-way conditionals, or numeric comparisons into pattern matching just for style.

## Responsibility Boundaries

Prefer one coherent reason to change. Large code can be acceptable when it expresses one workflow clearly. Small code can still be wrong when it mixes parsing, I/O, policy, formatting, and persistence.

## Tests

Test observable behavior and invariants. For functional core work, prefer focused tests around pure transformations and domain invariants. For shell/framework code, test enough integration behavior to prove wiring.

Avoid brittle tests that lock in helper names, internal call order, or incidental decomposition unless that shape is the contract.

## Documentation

Update durable docs only for durable choices: architecture-relevant exceptions, compatibility paths, persistence tradeoffs, or surprising constraints. Routine cleanup should not create doc churn.
