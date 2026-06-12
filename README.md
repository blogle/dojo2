# dojo

dojo is a local-first personal finance and envelope budgeting MVP. The repository now ships a DuckDB-backed FastAPI API, a Vue 3 frontend, fixture-backed onboarding/import flows, budget/account/transaction management, and hermetic Nix-based developer workflows.

## Status

The project is in first-draft MVP mode. A developer can import the bundled fixture sheet, land on a working budget dashboard, manage transactions and transfers, edit categories/accounts, and inspect current net worth locally.

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

On a fresh local database, open the web app and use `fixture://default` on the onboarding screen to seed deterministic demo data. When Google OAuth credentials are configured, the same flow can use a copied Google Sheet URL or ID.

## Verification Commands

- Tests: `just test`
- Lint: `just lint`
- Typecheck: `just typecheck`
- Build docs: `just docs`
- Build container: `just container`

## Repository Layout

- `api/` FastAPI backend under the `dojo` Python namespace, including DuckDB schema, SCD2 services, import logic, and API routes
- `web/` Vue 3 + TypeScript frontend under the `dojo` source namespace, including onboarding, budget, transactions, accounts, categories, and net worth views
- `docs/` mdBook user documentation
- `agents/` compact agent guidance
- `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md` developer source-of-truth docs

## CI

GitHub Actions installs Nix, enables Magic Nix Cache, then runs `just lint`, `just typecheck`, `just test`, and `nix build .#container`.

## Import Notes

- Fixture mode is controlled by `DEV_FIXTURE_MODE=true`
- Google OAuth stays fully environment-driven through `GOOGLE_OAUTH_*`
- The bundled fixture is the automated parity harness used by tests and local dogfooding
- The Google Sheets importer treats semantic named ranges as the authoritative source of spreadsheet data
- Granted Google OAuth access is held in backend memory for the current browser session instead of being written to disk
- Live Google validation still requires real credentials and a copied source sheet

## Documentation Model

- `SPEC.md` defines current scope and acceptance criteria
- `ARCHITECTURE.md` describes how the repository works now
- `DECISIONS.md` is the append-only technical decision log

## Agent Policy

Follow `AGENTS.md` for repository rules. Keep Dojo-specific agent guidance minimal and update docs alongside code.
