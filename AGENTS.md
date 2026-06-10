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

## Forbidden Actions

- Do not use React
- Do not bypass Nix for native tools
- Do not hardcode OAuth redirect URIs
- Do not create ADR/RFC directories
- Do not add large prompt libraries without a repeated observed need
- Do not delete stale docs; update them
