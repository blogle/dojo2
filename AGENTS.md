# dojo

Purpose: bootstrap a local-first personal finance application with a FastAPI API, a Vue 3 frontend, and a hermetic Nix-based workflow.

## Directory Map

- `api/` backend code and tests
- `web/` frontend code and tests
- `docs/` mdBook user docs
- `agents/` minimal agent guidance
- `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md` project docs

## Required Commands

- `just setup`
- `just lint`
- `just typecheck`
- `just test`
- `just docs`
- `just container`

Use `direnv + nix develop`. Do not rely on host-installed Python, Node, `uv`, `pnpm`, DuckDB, or `mdbook`.

## Hard Constraints

- Keep primary app directories as `api/` and `web/`
- Keep backend code under `api/src/dojo/`
- Keep frontend code under `web/src/dojo/`
- Use FastAPI for the API and Vue 3 for the web app
- Keep CI aligned with local `just` commands

## Documentation Rules

- Update `ARCHITECTURE.md` when code structure or runtime behavior changes
- Append new technical tradeoffs to `DECISIONS.md`
- Update `SPEC.md` only when scope or acceptance criteria change
- Do not delete stale docs; update them

## Testing Expectations

- Run the narrowest useful checks during implementation
- Before finishing, run lint, typecheck, tests, docs build, and container build when possible
- Report any command not run or any failing command

## ExecPlans

Use an ExecPlan for non-trivial implementation work: multi-file features, schema changes, significant refactors, public API changes, persistent data changes, Nix/devshell/CI/tooling changes, architecture changes, or work that may span more than one focused coding session.

ExecPlans are defined in `agents/execplan.md`.

Task-specific plans live in `plans/YYYY-MM-DD-short-task-name.md`.

An ExecPlan is a self-contained living implementation document. It must include purpose, context, progress, discoveries, decision log, concrete steps, validation, recovery notes, interfaces, and outcomes. Keep it updated as implementation proceeds.

Do not use ExecPlans as vague TODO lists. They must be specific enough for a stateless agent or novice human to resume the task from the plan alone.

## Forbidden Actions

- Do not use React
- Do not bypass Nix for native tools
- Do not hardcode OAuth redirect URIs
- Do not create ADR/RFC directories
- Do not add large prompt libraries without a repeated observed need
- Do not delete stale docs; update them
