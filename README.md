# dojo

dojo is a local-first personal finance application bootstrap. This repository currently provides a hermetic development environment, a minimal FastAPI API, a Vue 3 frontend shell, compact docs, and CI that mirrors local commands.

## Status

The project is in bootstrap mode. The initial application exposes health and status endpoints and a static frontend page that verifies the API is reachable.

## Prerequisites

- Nix
- direnv

Use `direnv + nix develop`. Do not rely on host-installed Python, Node, `uv`, `pnpm`, DuckDB, or `mdbook`.

## First-Time Setup

1. Enable direnv for the repository.
2. Run `direnv allow`.
3. Run `just setup`.

## Run The App

- API: `just dev-api`
- Web: `just dev-web`
- Combined guidance: `just dev`

## Verification Commands

- Tests: `just test`
- Lint: `just lint`
- Typecheck: `just typecheck`
- Build docs: `just docs`
- Build container: `just container`

## Repository Layout

- `api/` FastAPI backend under the `dojo` Python namespace
- `web/` Vue 3 + TypeScript frontend under the `dojo` source namespace
- `docs/` mdBook user documentation
- `agents/` compact agent guidance
- `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md` developer source-of-truth docs

## CI

GitHub Actions installs Nix, enables Magic Nix Cache, then runs `just lint`, `just typecheck`, `just test`, and `nix build .#container`.

## Documentation Model

- `SPEC.md` defines current scope and acceptance criteria
- `ARCHITECTURE.md` describes how the repository works now
- `DECISIONS.md` is the append-only technical decision log

## Agent Policy

Follow `AGENTS.md` for repository rules. Keep Dojo-specific agent guidance minimal and update docs alongside code.
