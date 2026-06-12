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

## Importer Note

The current budgeting implementation is allowlist-driven. Google Sheets named ranges are authoritative only when they are part of the consumed import contract. Unconsumed named ranges are deliberately ignored, including broken or legacy Aspire helper ranges. Consumed ranges are classified explicitly as `COLUMN_VECTOR`, `TABLE_BLOCK`, or `SCALAR_OR_LABEL` before validation and parsing. Visible category-group hierarchy and category ordering come from the `r_ConfigurationData` table block interpreted through consumed scalar row-symbol labels, while flat category vectors remain metadata-only. Aspire transaction vectors may also include structural or helper rows; dojo imports only amount-bearing real transactions from those vectors and skips amount-less structural rows while preserving strict validation for actual transactions. Amount-bearing transaction rows may import with a blank category as uncategorized transactions when they do not match a consumed system label, and may inherit the prior real transaction date when the sheet leaves a sparse date cell blank. Historical ledger references to hidden categories outside the visible configuration block are imported as hidden inactive categories rather than causing hard failures.
