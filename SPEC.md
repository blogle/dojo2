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
- `just setup`, `just build`, `just lint`, `just format-check`, `just typecheck`, `just test`, `just docs`, `just container`, `just bench-api` work in the Nix shell or fail with a documented reason
- `GET /api/transactions` supports pagination (`offset`, `limit`, `sort_by`, `sort_dir`) and returns `total`/`has_more` metadata
- Transaction list API responses are bounded to a single page instead of the full dataset
- The transactions page uses a bounded initial request window and bounded DOM rendering; it must not fetch or mount the full ledger for initial render
- Bootstrap stays a shell-sized payload and must not include full entity tables or the last full validation report
- Import benchmarking reports phase timings for realistic synthetic datasets, with a desired 10K import target under 5s when feasible and a tolerable ceiling under 10s
- Backend benchmark tests exist and are runnable via `just bench-api`

## Aggregate Correctness Criteria

Before additional budgeting functionality is accepted beyond the MVP import path, dojo must prove aggregate correctness for the financial values it already displays. The required correctness pass must:

- validate displayed account balances, pending balances, cleared balances, and credit-card display balances at exact-cent precision
- validate displayed category availability, month activity, month budgeted, clearly labeled starting-available values, Available to Budget, and budget-month summary totals against the imported source sheet semantics
- validate hidden-account and hidden-category behavior so default visible totals exclude hidden entities unless the UI explicitly enables them
- validate budget group totals for any totals displayed in the UI
- validate current net worth using ledger-derived budget-account balances and imported tracking valuations, while preserving duplicated imported budget-account net-worth rows only as ignored diagnostics
- expose a structured backend validation report with labels, source references, expected values, actual values, cent deltas, pass/fail state, and notes
- provide a deterministic fixture-backed validation path and a documented real-sheet validation path based on a copied Aspire sheet or saved fetch dump

Displayed aggregate labels must also be unambiguous:

- `Available to Budget` must match Aspire's dashboard value for the current imported workbook semantics and must not subtract liability starting-balance outflows
- if a prior-balance column is shown for categories or groups, it must be labeled as a starting-month value such as `Starting Available` rather than an unexplained carryforward term
- net-worth rows must always display a clear account or valuation label and must distinguish ledger-derived budget-account balances from imported valuation rows that are ignored in the native total

## Importer Note

The current budgeting implementation is allowlist-driven. Google Sheets named ranges are authoritative only when they are part of the consumed import contract. Unconsumed named ranges are deliberately ignored, including broken or legacy Aspire helper ranges. Consumed ranges are classified explicitly as `COLUMN_VECTOR`, `TABLE_BLOCK`, or `SCALAR_OR_LABEL` before validation and parsing. Visible category-group hierarchy and category ordering come from the `r_ConfigurationData` table block interpreted through consumed scalar row-symbol labels, while flat category vectors remain metadata-only. Aspire transaction vectors may also include structural or helper rows; dojo imports only amount-bearing real transactions from those vectors and skips amount-less structural rows while preserving strict validation for actual transactions. Amount-bearing transaction rows may import with a blank category as uncategorized transactions when they do not match a consumed system label, and may inherit the prior real transaction date when the sheet leaves a sparse date cell blank. Historical ledger references to hidden categories outside the visible configuration block are imported as hidden inactive categories rather than causing hard failures.
