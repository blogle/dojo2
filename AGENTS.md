# dojo

dojo is a local-first personal finance repository with a FastAPI API in `api/`, a Vue 3 frontend in `web/`, and repository-wide checks routed through the root `justfile`.

## First Commands

- `just setup`
- `just check`
- `just architecture-check`

## Command Policy

1. Treat the root `justfile` as the canonical interface for setup, development, verification, docs, benchmarks, and container tasks.
2. If a `just` recipe exists for the work you need to do, use it instead of invoking underlying tools directly.
3. Do not substitute ad hoc commands for `just` recipes merely for convenience.
4. If no suitable `just` recipe exists, use the underlying toolchain only for the missing step and say why.
5. Prefer the narrowest recipe that proves the change, then escalate to broader repo checks as needed.

Repository checks are authoritative. Do not claim success if the relevant `just` verification step has not been run, unless the user explicitly asked you not to run it or the environment blocks it.

## Authoritative Documents

- Overview: `README.md`
- Development workflow: `CONTRIBUTING.md`
- Product behavior: `SPEC.md`
- Visual and interaction design: `DESIGN.md`
- Current implementation: `ARCHITECTURE.md`
- Durable technical tradeoffs: `DECISIONS.md`

## Update Guide

| Change type | Update |
| --- | --- |
| Product behavior or acceptance criteria | `SPEC.md` |
| Visual design tokens, interaction patterns, or shared component specs | `DESIGN.md` |
| Runtime structure, persistence model, SQL organization, testing architecture | `ARCHITECTURE.md` |
| Durable technical decision or tradeoff | `DECISIONS.md` |
| Workflow, commands, repository policy guidance | `CONTRIBUTING.md` |
| Meaningful shipped or architectural change | `CHANGELOG.md` |

## Execution Guidelines

These rules are intentionally strict. They exist to keep agents from overreaching or drifting away from repository conventions.

### 1. Think Before Coding

- State assumptions explicitly when they affect implementation.
- If the request is ambiguous, ask instead of silently choosing a direction.
- Prefer the simpler interpretation unless the repo or user instruction clearly requires more.
- Read the relevant files first; do not infer architecture from filenames alone.

### 2. Simplicity First

- Implement only the behavior requested.
- Avoid speculative abstractions, flags, helpers, and configuration.
- Keep changes small and local unless the existing design requires otherwise.
- Match existing code style and patterns before introducing new structure.

### 3. Surgical Changes

- Touch only files and lines needed for the task.
- Do not refactor adjacent code unless it directly blocks the requested change.
- Remove only the dead code your own edits create.
- If you notice unrelated issues, mention them separately instead of folding them into the patch.

### 4. Goal-Driven Verification

- Translate the task into a concrete verification target before editing.
- Prefer adding or running the smallest relevant proof first, then broader checks.
- Use repository entrypoints for verification whenever they exist.
- Report what you verified and what remains unverified.

Short plan format for non-trivial work:

1. Inspect the relevant code and identify the smallest correct change.
2. Implement only that change.
3. Verify with the narrowest relevant `just` command, then broader commands if warranted.

