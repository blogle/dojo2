# Architecture

## Overview

dojo is bootstrapped as a two-application repository:

- `api/` contains a FastAPI service under `api/src/dojo/api/`
- `web/` contains a Vue 3 + TypeScript app under `web/src/dojo/`

The current implementation is intentionally small. The API exposes health and skeleton status endpoints. The web app renders a static landing page and calls the API status endpoint to confirm connectivity.

## Backend Skeleton

- Entry point: `dojo.api.main:app`
- Settings: `api/src/dojo/api/settings.py`
- Routes: `api/src/dojo/api/health.py`
- Tests: `api/tests/`

The backend reads environment-based settings through `pydantic-settings`. CORS origins are derived from environment configuration so the Vite app can call the API during local development.

## Frontend Skeleton

- Entry point: `web/src/main.ts`
- App namespace: `web/src/dojo/`
- Router: `web/src/dojo/router.ts`
- API client: `web/src/dojo/api/client.ts`
- Components: `web/src/dojo/components/`
- Styles: `web/src/dojo/styles/`
- Tests: `web/tests/`

The frontend uses a single route and simple component-local state. It fetches `/api/app/status` through a small fetch-based client configured by `VITE_API_BASE_URL`.

## Development Environment

- `flake.nix` defines the default dev shell
- `.envrc` loads the flake automatically through direnv
- Native tooling comes from Nix: Python, `uv`, Node, `pnpm`, `just`, DuckDB, `mdbook`, OpenSSL, `pkg-config`, `libffi`, `zlib`, and compiler toolchain pieces

Application dependencies remain language-managed inside `api/` and `web/`, but the native toolchain is hermetic.

## Build And CI

- `justfile` is the main developer entrypoint
- `.github/workflows/ci.yml` runs the same `just` commands used locally inside `nix develop`
- `packages.<system>.container` builds a Nix container image that starts the API skeleton on port `8000`

## Documentation Structure

- `SPEC.md` holds current bootstrap scope
- `ARCHITECTURE.md` tracks the current code shape
- `DECISIONS.md` records append-only technical decisions
- `docs/` contains user-facing mdBook documentation
- `agents/` contains only concise, Dojo-specific agent guidance
