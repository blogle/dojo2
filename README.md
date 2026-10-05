# dojo

dojo is a local-first personal finance application. The repository contains a FastAPI API, a Vue 3 frontend, a DuckDB-backed financial ledger, and repository-level quality gates that are intended to run the same way locally and in CI.

## Stack

- FastAPI in `api/`
- Vue 3 + TypeScript in `web/`
- DuckDB for local persistence
- Nix + direnv for native tooling
- `just` for canonical repository commands

## Setup

1. Install Nix and direnv.
2. Run `direnv allow` from the repository root.
3. Run `just setup`.

Use `direnv + nix develop`. Do not rely on host-installed Python, Node, `uv`, `pnpm`, DuckDB, or `mdbook`.

## Run The App

- API: `just api`
- Web: `just web`
- Combined guidance: `just dev`

`just api` explicitly provisions the DuckDB schema before starting the FastAPI server.

Generate the fictional development database with `just dev-fixture` (default repository path `api/.local/dev-fixture.duckdb`), then point the normal database setting at it: `DUCKDB_PATH=.local/dev-fixture.duckdb just api`. The generated database opens directly in the ready application; it does not use Aspire onboarding. Rerun `just dev-fixture` to reset local development data; pass another output path to create an isolated copy.

## Primary Checks

- Full local quality gate: `just check`
- CI-equivalent command: `just ci`
- Architecture and policy checks only: `just architecture-check`
- Backend and frontend tests: `just test`
- Fresh migration provisioning check: `just migration-check`
- Docs build: `just docs`
- Container build: `just container`

## Authoritative Documents

- Development workflow: `CONTRIBUTING.md`
- Agent routing: `AGENTS.md`
- Product behavior and acceptance criteria: `SPEC.md`
- Current implementation architecture: `ARCHITECTURE.md`
- Durable technical decisions: `DECISIONS.md`
- Meaningful changes: `CHANGELOG.md`
