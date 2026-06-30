---
name: justfile-infrastructure
description: justfile, just, setup, test, lint, format, build, docs, benchmark, container workflow guidance. Use when choosing repository commands or verification steps in dojo.
---

# Justfile Infrastructure

The root `justfile` is the canonical entrypoint for repository workflows.

## Rules

1. If a `just` recipe exists for the task, use it.
2. Do not replace `just` recipes with direct `uv`, `pnpm`, `pytest`, `ruff`, `mypy`, `mdbook`, or `nix` commands unless no recipe exists.
3. Prefer the narrowest recipe that verifies the change, then escalate only as needed.
4. When reporting results, name the exact `just` command you ran.
5. If a required workflow is missing from `justfile`, note the gap explicitly before using an underlying command.

## Canonical Commands

- Setup: `just setup`
- Dev: `just dev`, `just api`, `just web`
- Format: `just format`, `just format-check`
- Lint: `just lint`, `just lint-api`, `just lint-web`
- Typecheck: `just typecheck`
- Tests: `just test`, `just test-api`, `just test-web`, `just test-unit`, `just test-property`, `just test-integration`
- Build: `just build`, `just build-api`, `just build-web`
- Architecture: `just architecture-check`
- Migrations: `just migration-check`
- Docs: `just docs`
- Benchmarks: `just bench`, `just bench-api`, `just bench-web`
- Container: `just container`

## Selection Guidance

- Backend-only Python change: usually start with `just test-api` or a narrower backend test recipe.
- Frontend-only change: usually start with `just test-web`, plus `just lint-web` or `just typecheck` if relevant.
- Cross-cutting or risky change: prefer `just check`.
- Architecture or migration changes: include `just architecture-check` or `just migration-check`.

Do not claim the repository is green unless the relevant `just` verification step completed successfully.
