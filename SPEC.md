# dojo Bootstrap Spec

## Scope

Bootstrap the `dojo` repository with:

- `api/` FastAPI backend skeleton
- `web/` Vue 3 + TypeScript frontend skeleton
- Nix flake dev shell and container target
- direnv integration
- `just` developer workflows
- GitHub Actions CI that mirrors local commands
- compact project docs and minimal agent guidance

## Non-Goals

- Budgeting features
- Authentication or Google OAuth behavior
- DuckDB schema or import pipelines
- Production deployment infrastructure
- ADR/RFC directories or a large custom agent library

## Acceptance Criteria

- Health endpoints exist at `GET /health` and `GET /api/health`
- App status endpoint exists at `GET /api/app/status`
- Frontend renders `dojo`, shows skeleton status text, and checks API reachability
- Required root docs and `agents/` files exist and stay aligned with code
- `just setup`, `just build`, `just lint`, `just format-check`, `just typecheck`, `just test`, `just docs`, and `just container` work in the Nix shell or fail with a documented reason
