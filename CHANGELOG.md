# Changelog

## Unreleased

- Rewired Budget move, group funding, category/group creation, reorder saving, and retired-category restoration to persistent API operations with failure-visible UI behavior.
- Added aggregate validation and complete decision parsing to reviewed Aspire commits, including an executable reviewed-path fixture rehearsal.
- Added transaction version tokens, stale-write conflicts, and success-only transaction form, undo, and removal feedback.
- Added manifest-verified DuckDB backup/restore commands, OpenEBS ZFS snapshot orchestration, encrypted rotating restic backups through rclone to Google Drive, and new-PVC restore resources.

- Added account-local reconciliation drafts, persisted source evidence, digest-checked idempotent apply with explicit balance adjustments, reopening status, working-set/history endpoints, and a balance-first budget-account action.
- Fixed first-run onboarding and Aspire migration when the development frontend is opened from a non-localhost address by routing default browser API traffic through Vite's same-origin proxy and binding OAuth callbacks to the initiating session and frontend origin, with regression coverage for both paths.
- Added a deterministic Cypress browser-acceptance harness with API-owned scenario resets, XDG-cached DuckDB baselines, Chromium execution, per-phase timing reports, and initial cross-surface Assets & Liabilities coverage.
- Added type-aware tracking, tangible, investment, and loan value flows; account-configured contribution/payment categories; same-day provisional investment ordering; transfer provenance; derived category activity/history; cross-surface loan payment activity; cash-only investment statements; future-date guards; opening loan principal; lender YTD checkpoints; estimated amortization; separately presented restricted escrow; and atomic one-to-many tracking cutover.
- Added the Assets & Liabilities Add item wizard with an explicit `/assets-liabilities/add` route, entity-type selection, minimal type-specific account forms, and Cypress coverage for route safety and account creation payloads.
- Added `POST /api/transactions/{transaction_id}/restore` endpoint for SCD-correct undo of deleted transactions, preserving the same `transaction_id` across delete/restore cycles with full audit history.
- Added pure SCD algebra/model with Hypothesis property-based testing to validate SCD invariants (no overlapping intervals, single current version, as-of stability) before shipping the restore endpoint.
- Updated frontend undo stack to use restore endpoint instead of create, ensuring deleted transactions are restored with the same `transaction_id`.
- Added checked-in Cypress component-testing harness for the Vue frontend, wired `just test-web` through both Vitest and Cypress component runs, and left `just test-e2e` reserved for the still-missing deterministic browser e2e layer.
- Added explicit DuckDB provisioning through `api/src/dojo/migrations.py`, moved schema SQL into native `.sql` files, and stopped `Database(...)` from creating or migrating schema as a hidden side effect.
- Added a central backend clock abstraction plus deterministic test clocks, reusable SCD2 invariant assertions, fresh-database provisioning tests, and Hypothesis coverage for real allocation, transfer, status-change, and transaction-history behavior.
- Added repository architecture and policy checks for direct DuckDB connections, direct wall-clock usage, router boundary violations, large inline SQL, SQL f-strings, SQL file location, test-only imports, and persisted money type rules.
- Added `CONTRIBUTING.md` as the canonical development guide, shortened `AGENTS.md` to routing guidance, and aligned CI with the canonical `just ci` command.

- Completed the interactive transaction-table path: the frontend now keeps only one server-driven transaction page in reactive state, requests `limit=100` for the initial page, uses previous/next page controls, and relies on the existing virtual table to keep DOM rows bounded.
- Reused precomputed category lists for both `get_budget` and `GET /api/categories`, so grouped budget responses are shaped once instead of recomputing the same month twice.
- Batched full-import SCD writes across category groups, accounts, categories, budget buckets, budget-account settings, transactions, allocations, and net-worth valuations. The local synthetic 10K import profile is now about 9.5s, with the remaining cost concentrated in transaction writes and post-import aggregate snapshot work.
- Reused cached account and default-month category data inside `snapshot_for_validation()` so post-import aggregate checks avoid redundant list/account/group recomputation.
- Slimmed bootstrap to an app-shell payload: `GET /api/bootstrap` now returns only `app_status`, `import_status`, and `default_budget_month`, and bootstrap/status payloads no longer include the last full validation report. Fixture bootstrap payload dropped from about 248,619 bytes to about 2,296 bytes.
- Added benchmark coverage for transaction window payload sizes, budget shaping costs, bootstrap payload size, and import phase timings across 1K and 10K synthetic datasets.
- Added regression coverage for bounded transaction paging, bounded DOM rendering, paginated transaction API semantics, and a bootstrap payload-size ceiling.
- Added backend benchmark infrastructure: synthetic dataset generator, wall-clock Timer, DuckDB EXPLAIN ANALYZE wrapper, and parameterized benchmark tests for all query/formula domains (transactions, categories, budget, accounts, ATB, net worth, hidden filtering, import speed) at 1K/10K/100K transaction scales.
- Added API route-level benchmarks with timing and response payload size measurement for all major endpoints.
- Added `just bench`, `just bench-api`, `just bench-api-quick`, `just bench-api-routes`, `just bench-api-report`, and `just bench-web` commands.
- Optimized `list_categories` to precompute transaction and allocation aggregates with SQL GROUP BY instead of per-category N+1 Python loops. 1K dataset: 451ms → 20ms (22x). 10K dataset: 9,324ms → 75ms (124x).
- Optimized `get_budget` which called both `list_categories` and `list_category_groups` (duplicating work). 1K dataset: 896ms → 72ms (12x). 10K dataset: 19,724ms → 225ms (88x).
- Added server-side pagination to `GET /api/transactions`: `offset`, `limit`, `sort_by`, `sort_dir` query parameters, with `total`, `offset`, `limit`, `has_more` metadata in response. Hidden-entity filtering now uses SQL WHERE clauses instead of Python-side post-filtering.
- Measured API payload sizes: budget/bootstrap endpoints return 1-300KB; transactions with `limit=50` return ~8KB instead of full-table payload. Documented that the previous implementation loaded the full transaction array into client memory (frontend `limit=2000` hardcoded).
- Added a first-class aggregate validation harness and CLI command so fixture imports and saved real-sheet fetch dumps can be audited with structured labeled checks, cent deltas, source references, and pass/fail notes.
- Corrected Available to Budget semantics to match Aspire's `Dashboard!J3` / `Calculations!B59` behavior, including counting starting-balance inflows without subtracting liability starting-balance outflows.
- Aligned the backend's default budget month with the current calendar month so the default budget view matches Aspire's current dashboard month instead of the last imported ledger month.
- Corrected net-worth rows so every ledger-derived item has an explicit label, normalized duplicate budget-account valuations are ignored in native net worth, and ambiguous duplicate matches fail validation instead of silently double-counting.
- Replaced the ambiguous user-facing `Carried over` label with `Starting Available` on budget tables and removed the top-level carryforward summary metric.
- Corrected budget summary spending totals so hidden-category spending is excluded from the default visible budget summary and only included when hidden entities are explicitly shown.
- Added backend/API/frontend aggregate correctness tests covering account balances, category values, group totals, Available to Budget, hidden-entity behavior, credit-card display behavior, and net worth presentation.
- Tightened aggregate UI labeling by adding backend-provided budget group totals, labeled budget columns, explicit account balance labeling, an accounts-page hidden toggle, and clearer net-worth total/source text.
- Implemented the browser-driven Google OAuth flow in the web app, stopped persisting Sheets access tokens to disk, and now keep granted tokens only in backend memory for the active browser session.
- Corrected the importer's named-range model to support `COLUMN_VECTOR`, `TABLE_BLOCK`, and `SCALAR_OR_LABEL` shapes, including rectangular configuration blocks and scalar sheet symbols.
- Simplified the importer to an explicit allowlist contract so broken or irrelevant Aspire named ranges such as `trx_Uuids` are ignored instead of being validated.
- Corrected category-group import so visible group membership and display ordering come from walking `r_ConfigurationData` with consumed scalar row symbols, while `UserDefCategories` and related flat vectors remain metadata-only.
- Corrected transaction parsing so Aspire helper, reconciliation, break, and other amount-less structural rows embedded in transaction named ranges are classified and skipped instead of failing import, while amount-bearing rows still receive strict validation.
- Corrected live-sheet transaction import to allow uncategorized amount-bearing transactions with blank category cells, and added bootstrap migration support for older DuckDB transaction constraints that previously rejected them.
- Corrected live-sheet transaction import to skip pending staged rows that carry an amount and memo but still have no account or category, instead of treating them as malformed real transactions.
- Corrected live-sheet transaction import to carry forward the prior real transaction date for sparse amount-bearing rows with a blank date cell when the intended date is inherited from the preceding row.
- Corrected live-sheet allocation import to skip zero-dollar no-op rows while still rejecting negative or malformed allocation amounts.
- Added a repository-local live-sheet harness that fetches the allowlisted Google Sheet named ranges into a temporary DuckDB import loop with cached OAuth state for direct importer debugging.
- Refactored the Google Sheets importer to use centralized named-range discovery and validation instead of header-scanning tables.
- Implemented the first working budgeting MVP: DuckDB schema and SCD2 history, fixture-backed onboarding/import validation, budget formulas, API endpoints, Vue workflows for budgeting/accounts/transactions/categories/net worth, and expanded backend/frontend automated coverage.
- Strengthened the ExecPlan agent skill into a self-contained living-plan workflow for complex implementation tasks.
- Bootstrapped project skeleton.
