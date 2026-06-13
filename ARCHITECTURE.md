# Architecture

## Overview

dojo is a two-application repository with a local-first budgeting stack:

- `api/` contains a FastAPI service under `api/src/dojo/`
- `web/` contains a Vue 3 + TypeScript app under `web/src/dojo/`

The implemented MVP is DuckDB-backed and versioned with SCD2 validity intervals. The backend owns the budgeting ledger, import pipeline, and formula semantics; the frontend owns onboarding plus daily budget/account/transaction workflows.

## Backend

- Entry point: `api/src/dojo/api/main.py`
- Settings: `api/src/dojo/api/settings.py`
- API routes: `api/src/dojo/api/routes.py`
- DuckDB lifecycle: `api/src/dojo/database.py`
- Schema bootstrap: `api/src/dojo/schema.py`
- SCD helpers: `api/src/dojo/scd.py`
- Import parsing and fixtures: `api/src/dojo/importer.py`, `api/src/dojo/fixture_data.py`, `api/src/dojo/google.py`
- Aggregate validation harness: `api/src/dojo/aggregate_validation.py`, `api/src/dojo/validation_cli.py`
- Domain/service layer: `api/src/dojo/service.py`
- Tests: `api/tests/`

The backend uses one DuckDB connection and an application-level lock. Schema bootstrap creates the SCD2 domain tables from the MVP spec: `accounts`, `budget_account_settings`, `category_groups`, `categories`, `budget_buckets`, `transactions`, `allocations`, `net_worth_valuations`, plus `import_runs` and `import_batches`. Current-state access is exposed through `current_*` views, while history is preserved via `valid_from`/`valid_to` replacement semantics.

The `DojoService` computes account balances, ATB, category availability, month activity, month budgeted values, starting-available values, credit-card payment availability, group totals, and net worth rollups directly from current ledger tables. Import validation no longer relies on a coarse fixture snapshot. `api/src/dojo/aggregate_validation.py` builds a structured aggregate report from the parsed import bundle plus the persisted DuckDB state and records labeled pass/fail checks with source references, expected values, actual values, cent deltas, and notes. `python -m dojo.validation_cli --fixture` reruns the same validation path against the deterministic fixture, and `python -m dojo.validation_cli --fetch-dump <path>` reruns it against a saved live-sheet fetch dump.

The importer is named-range-first and allowlist-driven. `api/src/dojo/importer.py` centralizes the consumed named-range contract: only the ranges needed by the MVP are discovered, fetched, validated, and parsed. Everything outside that contract is ignored, including broken Aspire helper names, UUID ranges, dashboard/report implementation details, and legacy internals. Consumed ranges are classified explicitly as `COLUMN_VECTOR`, `TABLE_BLOCK`, or `SCALAR_OR_LABEL`. Ledger vectors are validated as single-column and zipped with trailing-blank padding, explicitly consumed table blocks are parsed as rectangles, and consumed scalar constants such as status/system labels are read as single values. Transaction vectors are classified row-by-row so blank, break, reconciliation, staged-helper, and other non-ledger rows are skipped while amount-bearing rows still receive strict validation; amount-bearing rows may still import with no category as uncategorized transactions when no system label is present, and sparse live-sheet rows may inherit the most recent prior transaction date when the date cell is blank. Allocation vectors still validate positive movement semantics, but zero-dollar no-op rows are skipped. Category-group structure now comes from walking `r_ConfigurationData` in display order with scalar row-symbol labels, while `UserDefCategories`/`UserDefAmounts`/`UserDefGoals` remain metadata vectors instead of a source of group membership. When historical transactions or allocations still reference hidden categories absent from the visible configuration block, the importer synthesizes hidden inactive categories under an importer-owned hidden group so legacy history can load without changing visible structure. Literal named-range strings stay centralized in that contract, and header parsing is no longer the primary import mechanism.

Aggregate validation uses the same consumed named-range contract as the import path, but it treats source-of-truth boundaries explicitly:

- account, category, ATB, group-total, and month-summary checks compare persisted dojo aggregates against the interpreted imported source ledger
- hidden-account and hidden-category checks validate both metadata preservation and default visible-list exclusion
- budget-account net worth is derived from current budget-account balances in the ledger
- imported net-worth rows for those same budget accounts are preserved as diagnostic rows and marked ignored instead of counted in the total

The corrected ATB rule matches Aspire's current workbook formula at `Calculations!B59`, rendered on `Dashboard!J3`. dojo computes ATB from:

- ATB-category inflows and outflows
- starting-balance inflows only
- balance-adjustment inflows and outflows on budget accounts
- category-transfer rows into and out of the ATB bucket

Credit-card or other liability starting-balance outflows do not reduce ATB. The fixture and live-sheet validation checks now enforce that rule.

The current budget month is date-driven rather than ledger-tail-driven. The frontend budget page and backend `default_budget_month()` both use the current calendar month so the default budget view aligns with Aspire's dashboard month even when no newer transactions or allocations have been imported yet.

The user-facing category column previously called `Carried over` is now treated as `Starting Available`: the category balance at the start of the selected month before current-month budgeted movement and activity. The top-level budget summary no longer displays an unexplained carryforward metric.

Net-worth duplicate handling is now explicit. Import-time matching first prefers exact budget-account name matches, then a normalized-name match that strips decorative emoji, spacing, and punctuation. When exactly one budget account matches, dojo treats the imported valuation as a duplicate diagnostic row and excludes it from native net worth. When multiple budget accounts match the same normalized valuation name, dojo marks the valuation as an ambiguous duplicate, excludes it from the native total, and fails aggregate validation so the mismatch is visible instead of silently double-counted.

Google OAuth is initiated by `/api/onboarding/google/start`, completed at `/api/onboarding/google/callback`, and stored only in backend memory for the current browser session. Local fixture mode bypasses the credential requirement for automated tests and first-pass dogfooding.

## Frontend

- Entry point: `web/src/main.ts`
- App namespace: `web/src/dojo/`
- Router: `web/src/dojo/router.ts`
- API client: `web/src/dojo/api/client.ts`
- Global state composable: `web/src/dojo/state/app.ts`
- Pages: `web/src/dojo/pages/`
- Components: `web/src/dojo/components/`
- Styles: `web/src/dojo/styles/`
- Tests: `web/tests/`

The frontend uses Vue Router plus a shared composable store. On startup it fetches a small bootstrap payload with readiness state plus the default budget month, redirects to onboarding when no successful import exists, and otherwise fetches budget, transactions, accounts, categories, and net-worth data on demand.

UI flows are intentionally operational rather than decorative:

- onboarding/import status with fixture or Google entry
- budget dashboard with ATB, month metrics, hidden-entity toggle, labeled category columns including starting available, and backend-provided group totals
- transaction entry/edit/delete/status toggle plus transfer helper
- account cards with explicit balance labeling plus account-detail transaction list
- category/group/account creation and visibility management
- minimal current net worth view with explicit current-total labeling, labeled ledger rows, and ignored budget-account or ambiguous duplicate import values surfaced explicitly

Transaction-heavy views use `VirtualDataTable`/`VirtualTransactionTable`, which render only the visible window plus overscan so large ledgers do not mount every row at once.

Styling uses CSS variables and Tailwind-enabled build plumbing to express the earth-tone brutalist system from the MVP spec: dense tables, square edges, low decoration, off-white paper backgrounds, muted greens, and monospace financial values.

## Development Environment

- `flake.nix` defines the default dev shell
- `.envrc` loads the flake automatically through direnv
- Native tooling comes from Nix: Python, `uv`, Node, `pnpm`, `just`, DuckDB, `mdbook`, OpenSSL, `pkg-config`, `libffi`, `zlib`, and compiler toolchain pieces

Application dependencies remain language-managed inside `api/` and `web/`, but the native toolchain is hermetic. Python linting is invoked through `uv run python -m ruff ...` so the repo does not depend on a host or shell-specific standalone Ruff binary.

## Build And CI

- `justfile` is the main developer entrypoint
- `.github/workflows/ci.yml` runs the same `just` commands used locally inside `nix develop`
- `packages.<system>.container` builds a Nix container image that starts the API on port `8000`

Routine verification is still driven by `just setup`, `just lint`, `just typecheck`, `just test`, `just docs`, and `just container`.

## Performance Architecture

### Benchmark Infrastructure

- **Synthetic datasets**: `api/src/dojo/benchmark_fixtures.py` generates deterministic synthetic `ParsedImportBundle` objects at three scales: 1K (5 accounts, 10 categories, 3 months), 10K (10 accounts, 25 categories, 12 months), and 100K (20 accounts, 50 categories, 24 months). Datasets include budget and tracking accounts, standard and credit-card-payment categories, starting-balance entries, distributed transactions, monthly allocations, and net-worth valuations.
- **Timing**: `api/src/dojo/benchmarks.py` provides a `Timer` context manager (wall-clock via `time.perf_counter`), `explain_analyze()` wrapping DuckDB `EXPLAIN ANALYZE`, and a `run_backend_benchmarks()` runner that exercises every query/formula path per dataset.
- **Running**: `just bench-api` runs backend benchmark tests (pytest with `-s` for visible timings). `just bench-api-report` runs the full suite across all dataset sizes. `just bench-web` runs frontend performance tests.

### Current Measured Performance (post-optimization)

| Operation | 1K (ms) | 10K (ms) |
|-----------|---------|----------|
| transaction window `limit=100` | ~32-44 | ~40-44 |
| list_categories | ~55-61 | ~285 |
| list_category_groups from precomputed categories | ~6 | ~5.5 |
| get_budget | ~115-123 | ~718 |
| get_bootstrap (synthetic service payload) | ~13 | ~16 |
| import profile total | ~1,003 | ~9,491 |
| import write_transactions phase | ~560 | ~5,007 |
| import post_import_snapshot phase | ~294 | ~3,872 |

Fixture API-route payload sizes after this pass:

- `GET /api/transactions?limit=50`: ~6.8 KB
- `GET /api/budget`: ~4.8 KB
- `GET /api/accounts`: ~3.2 KB
- `GET /api/categories`: ~7.6 KB
- `GET /api/net-worth`: ~5.9 KB
- `GET /api/bootstrap`: ~2.3 KB

*Wall-clock milliseconds from the local benchmark suite using DuckDB in-memory synthetic datasets unless otherwise noted.*

### Known Bottlenecks

1. **Import speed**: The 10K synthetic import profile now lands just under the tolerable 10s ceiling, but the dominant remaining phases are still transaction writes and post-import aggregate snapshot work. If import needs to move materially below that ceiling, the next likely wins are a more efficient bulk-load primitive for transactions and deeper aggregate-validation-path optimization.

2. **Credit-card payment category computation**: Each CC payment category triggers two additional DB queries (CC spend + transfer adjustment). For typical datasets with 1-3 CC accounts this is negligible, but the queries could be batched for larger deployments.

### Transaction Data Path

- `GET /api/transactions` returns only the requested page with `total`, `offset`, `limit`, and `has_more` metadata.
- Hidden-entity filtering is server-side through the existing `show_hidden` parameter rather than client-side post-filtering.
- The frontend requests `limit=100` for the initial page and keeps only the current page in reactive state.
- Pagination is explicit with previous/next controls. The client does not accumulate the entire ledger as the user pages.
- Ordering is server-driven. The current frontend path requests `sort_by=date&sort_dir=desc`, so no client-side sort of partial pages can drift from backend order.

### Paginated Transaction API

`GET /api/transactions` supports:
- `limit` (default 500, max 10,000)
- `offset` (default 0)
- `show_hidden` (default false)
- `sort_by` (date, amount_minor, status, created_at)
- `sort_dir` (asc, desc)

Response shape:
```json
{
  "items": [...],
  "total": 12345,
  "offset": 0,
  "limit": 50,
  "has_more": true
}
```

### Frontend Rendering

Transaction-heavy views use `VirtualDataTable`/`VirtualTransactionTable` which render only the visible window plus overscan (6 rows) via CSS spacer divs. This prevents DOM flooding for large datasets. Transactions are now loaded in server-driven pages of 100 via `fetchTransactionsPage`; the page controls swap the current page instead of appending into a growing client-side ledger array.

### Bootstrap Payload Policy

- Bootstrap is an app-shell payload, not a data dump.
- `GET /api/bootstrap` now returns only `app_status`, `import_status`, and `default_budget_month`.
- Bootstrap and app-status paths no longer carry the last full validation report, which was the main source of the earlier 249 KB fixture payload.
- Accounts, budget groups/categories, transactions, and net worth are fetched on demand after bootstrap when the app is ready.

### Budget Aggregate Shaping

- `get_budget()` computes the category list once and shapes group totals from those precomputed categories.
- `GET /api/categories` now follows the same pattern instead of calling `list_categories()` once for groups and again for flat items.

### Import Batch Write Strategy

- `_insert_bundle()` prepares row dictionaries in memory and batches inserts per table for category groups, accounts, categories, budget buckets, budget-account settings, transactions, allocations, and net-worth valuations.
- Transactions remain the dominant write phase, but batching the smaller dimension tables removed a large amount of per-row DuckDB overhead.
- `snapshot_for_validation()` now reuses already-fetched accounts and default-month category data so post-import aggregate checks avoid redundant work.

## Documentation Structure

- `SPEC.md` holds current bootstrap scope
- `ARCHITECTURE.md` tracks the current code shape
- `DECISIONS.md` records append-only technical decisions
- `docs/` contains user-facing mdBook documentation
- `agents/` contains only concise, Dojo-specific agent guidance
