# Decisions

## 2026-06-12 — Add server-side pagination to the transaction API

### Context

The original `GET /api/transactions` returned all matching rows with a Python-side `LIMIT` applied after fetching the full result set. The frontend loaded up to `limit=2000` transactions into client memory with no pagination metadata. For datasets of 10K+ transactions, this meant uploading hundreds of kilobytes to the browser on every page load and after every write operation.

### Decision

Add server-side pagination with `offset`/`limit` parameters, `sort_by`/`sort_dir` sorting, and pagination metadata (`total`, `offset`, `limit`, `has_more`). Move hidden-entity filtering from Python-side loops to SQL WHERE clauses. Keep the existing `limit` parameter as the page size (default 500, max 10,000).

### Consequence

- Transaction list responses are bounded to a single page of rows rather than the full dataset.
- Frontend can implement incremental loading or pagination controls without receiving the entire ledger.
- Backward compatible: existing clients that only use `limit` continue to work; the response shape now includes `total`/`has_more` fields in addition to `items`.

## 2026-06-12 — Optimize category aggregates with SQL precomputation instead of per-category Python loops

### Context

`list_categories` previously iterated over N categories and for each called 4 functions (`compute_category_available`, `compute_month_activity`, `compute_month_budgeted`, `compute_carried_over`). Each function fetched the full transactions and allocations tables from DuckDB and filtered in Python. With 10K transactions and 25 categories, this took >9 seconds and was O(N * (T + A)).

### Decision

Precompute transaction sums per category and allocation sums per bucket in a single pass each (SQL GROUP BY in Python dicts), then join in a single Python pass per category. For credit-card payment categories, batch the CC-specific queries per linked account.

### Consequence

- `list_categories` at 10K/25 categories: 9,324ms → 75ms (124x faster).
- `get_budget` at 10K (calls list_categories + list_category_groups): 19,724ms → 225ms (88x faster).
- The tradeoff is slightly more code in `list_categories` and two additional DB queries per CC payment category (negligible for 1-3 CC accounts).

## 2026-06-12 — Keep the transaction table bounded to one server-driven page plus DOM virtualization

### Context

The backend pagination work removed full-ledger API responses, but the frontend still accumulated fetched pages into one growing reactive array. That kept DOM nodes bounded because of virtualization, but client memory still trended toward a shadow copy of the ledger.

### Decision

Keep the existing focused `VirtualDataTable` windowing component, but make the transaction page itself server-driven and page-bounded. The frontend now requests `limit=100` pages from `/api/transactions`, keeps only the current page in state, and uses previous/next controls instead of append-only client paging.

### Consequence

- Initial transaction render stays bounded in both API payload and client state.
- DOM rendering remains bounded by the existing virtualization layer.
- Ordering semantics stay server-side (`sort_by=date&sort_dir=desc` in the current UI path), so partial pages are not re-sorted client-side.

## 2026-06-12 — Keep bootstrap app-shell sized and exclude full validation reports

### Context

The previous bootstrap path returned large entity arrays and the most recent full import validation report. On the fixture dataset that pushed `GET /api/bootstrap` to roughly 249 KB even though the frontend immediately fetched the real budget, transactions, accounts, and net-worth payloads separately.

### Decision

Treat bootstrap as an app-shell payload only. Return `app_status`, `import_status`, and `default_budget_month`, and strip `validation_report` from bootstrap and status-path import-run summaries.

### Consequence

- Fixture bootstrap shrank to about 2.3 KB.
- Startup no longer duplicates a large validation-report payload on the status/bootstrap path.
- The frontend relies on follow-up endpoint fetches for budget, accounts, transactions, and net worth once the app is known to be ready.

## 2026-06-12 — Batch full-import SCD writes per table before considering deeper import rewrites

### Context

Import profiling showed that even after transaction and allocation batching, row-wise inserts for category groups, accounts, categories, buckets, settings, and valuations still added material latency. The dominant phases were still write-heavy, but the remaining row-by-row calls were easy measured overhead.

### Decision

Prepare row dictionaries in memory and batch insert every import table that participates in the initial full-load path. Keep SCD2 validity semantics unchanged and keep the optimization limited to the existing initial-load import flow instead of introducing temp-table diffing or caching.

### Consequence

- The 10K synthetic import profile moved from roughly 12s down to roughly 9.5s, with the remaining dominant phases now clearly visible as transaction writes and post-import aggregate snapshot work.
- The import path stays readable and history-preserving, while leaving room for a future temp-table or COPY-style bulk-load path if import volume grows.

## 2026-06-10 — Use Nix, direnv, and just for local development

### Context

The project needs a repeatable local environment without depending on host-installed native tooling.

### Decision

Use a Nix flake for the dev shell, `direnv` for automatic shell loading, and `just` for routine commands.

### Consequence

Native dependencies are centralized in `flake.nix`, local and CI workflows stay aligned, and contributors should not install ad hoc system packages for repo work.

## 2026-06-10 — Use Vue 3 instead of React for the frontend skeleton

### Context

The bootstrap needs a minimal frontend framework choice before feature work begins.

### Decision

Use Vue 3 with TypeScript and Vite for the initial frontend skeleton.

### Consequence

Frontend code, tests, and tooling are aligned around Vue patterns, and React-based alternatives are out of scope unless a later decision supersedes this one.

## 2026-06-10 — Use the Three-File Strategy for developer docs

### Context

The repository needs durable technical context without scattering documents across RFC or ADR directories.

### Decision

Use `SPEC.md`, `ARCHITECTURE.md`, and `DECISIONS.md` as the root developer documentation model.

### Consequence

Project scope, current structure, and historical tradeoffs live in predictable places, and RFC/ADR directory trees are explicitly avoided.

## 2026-06-10 — Keep agent guidance minimal and Dojo-specific

### Context

Bootstrap should help coding agents operate safely without creating a large speculative prompt library.

### Decision

Keep `AGENTS.md` concise and limit `agents/` to a small README, an execplan template, and Nix boundary guidance.

### Consequence

Agent context stays compact, custom instructions remain maintainable, and new specialized prompts require repeated evidence of need.

## 2026-06-10 — Add CI during bootstrap and mirror local commands

### Context

The skeleton should validate its environment and workflows before application complexity increases.

### Decision

Add GitHub Actions CI now and make it run the same `just` commands developers use locally, plus the Nix container build.

### Consequence

Local and remote verification stay consistent, and changes to workflow commands should happen in one place instead of diverging between CI and development.

## 2026-06-10 — Adopt self-contained ExecPlans for complex implementation work

### Context

The initial `agents/execplan.md` was too lightweight. It provided a simple planning checklist but did not capture enough context, validation, discoveries, or decision history for a stateless coding agent to safely resume complex work.

### Decision

Adopt a self-contained living ExecPlan workflow for non-trivial implementation tasks. Task-specific plans live under `plans/`, while the reusable skill definition lives in `agents/execplan.md`.

### Consequence

Complex work now has a durable task-local source of truth with progress, discoveries, decision log, validation, and recovery notes. This adds a small amount of process overhead, but only for work where the added structure reduces implementation risk. Durable architectural decisions must still be copied into `DECISIONS.md`.

## 2026-06-10 — Validate imports against a deterministic fixture harness first

### Context

The MVP requires penny-accurate import validation, but the repository does not include real Google credentials or a checked-in copy of the operational spreadsheet.

### Decision

Implement the import pipeline so it can read either a live Google Sheet or a repository fixture, and make the fixture the automated validation source used by tests and local dogfooding.

### Consequence

The app can be exercised end-to-end in CI and local development without secrets, while the live Google path remains available for manual validation once credentials exist. Real-sheet parity is still a follow-up verification step rather than something silently assumed.

## 2026-06-10 — Invoke Ruff through `python -m ruff` inside `uv`

### Context

The standalone Ruff executable exposed in this environment is not consistently runnable through Nix stub-ld boundaries.

### Decision

Run Ruff as `uv run python -m ruff ...` from project workflows instead of depending on a standalone `ruff` binary.

### Consequence

Linting remains hermetic and reproducible under the repo-managed Python environment, and `just` commands no longer rely on a shell-specific Ruff installation detail.

## 2026-06-10 — Make named ranges the authoritative spreadsheet import contract

### Context

Header-scanning visual tables is brittle for long-lived budgeting spreadsheets because decorative rows, layout drift, and optional columns can move independently of the semantic data the app actually needs.

### Decision

Make Google Sheets named ranges the authoritative importer contract. Discover actual workbook names once from metadata, map them into one centralized importer alias table, validate required ranges and compatible lengths up front, and build domain rows by zipping named-range columns.

### Consequence

The importer no longer guesses table bounds from visual headers. Real-sheet compatibility now depends on named-range coverage and validation rather than layout heuristics, and any remaining header parsing must stay fallback-only for clearly optional fields.

## 2026-06-10 — Keep Google OAuth access tokens only in backend memory

### Context

The first OAuth pass wrote granted Google Sheets tokens to a local file. For a local-first budgeting app, that creates avoidable secret persistence and a rougher user trust model than necessary.

### Decision

Keep granted Google OAuth tokens only in backend memory, keyed to an opaque browser-session identifier, and require re-authorization after backend restart instead of persisting tokens to disk.

### Consequence

The Google Sheets import flow is safer by default because tokens are not written to the repository or workstation filesystem by the app. The tradeoff is that OAuth access must be re-established when the backend process restarts.

## 2026-06-11 — Keep named ranges authoritative, but handle shapes explicitly

### Context

Aspire-style Sheets use named ranges for different semantic forms: row-zipped ledger vectors, rectangular configuration/report blocks, and scalar label constants. Treating every named range as a single-column vector breaks valid ranges such as `r_ConfigurationData`.

### Decision

Keep named ranges authoritative, but classify each one explicitly as `COLUMN_VECTOR`, `TABLE_BLOCK`, or `SCALAR_OR_LABEL` in one centralized importer contract before validation or parsing.

### Consequence

The importer can validate and parse ledger vectors, configuration blocks, and scalar symbols correctly without falling back to visual table heuristics or misclassifying rectangular blocks as invalid vectors.

## 2026-06-11 — Ignore unconsumed Aspire named ranges entirely

### Context

Aspire workbooks include many helper, dashboard, UUID, script, broken, and legacy named ranges that are irrelevant to dojo's MVP import path. Reading or validating all of them makes the importer fragile and couples dojo to Aspire internals.

### Decision

Make the importer allowlist-driven: only named ranges in dojo's explicit consumed contract are discovered, fetched, validated, and parsed. Unconsumed named ranges are ignored entirely, even when they are broken.

### Consequence

The importer stops failing on irrelevant workbook internals such as broken UUID ranges, and dojo stays coupled only to the subset of named ranges it actually consumes for MVP parity.

## 2026-06-11 — Derive category hierarchy from `r_ConfigurationData`

### Context

`UserDefCategories` and related flat vectors carry category metadata, but they do not preserve visible category-group boundaries or display ordering. Aspire's rectangular `r_ConfigurationData` block encodes that structure through row symbols.

### Decision

Derive visible category-group membership and ordering by walking `r_ConfigurationData` as a `TABLE_BLOCK`, using consumed scalar named ranges for the group, reportable-category, non-reportable-category, and debt or credit-card-payment row symbols. Keep flat category vectors for metadata only.

### Consequence

dojo now preserves sheet display order and group boundaries without inferring structure from lossy vectors or hardcoded row glyphs. The importer remains allowlist-driven because it consumes only `r_ConfigurationData` plus the scalar symbols needed to interpret that block.

## 2026-06-11 — Classify transaction rows before validating them

### Context

Aspire transaction named ranges can contain structural, reconciliation, pending-staging, and sparse-display rows alongside real amount-bearing transactions. Treating every nonblank row as a transaction caused live-sheet imports to fail on helper rows and inherited-date display patterns.

### Decision

Classify transaction rows before validation. Skip blank, break, reconciliation, helper, and pending staged rows that do not represent committed ledger movement. For real amount-bearing rows, keep strict validation, but allow uncategorized transactions, allow inherited dates from the most recent prior real transaction when the sheet leaves the date cell blank, and continue reading system labels from consumed scalar named ranges.

### Consequence

dojo stays strict about real transaction integrity without coupling itself to every Aspire sheet-display convention. Live imports can now tolerate helper rows and sparse transaction formatting while still failing true malformed transactions.

## 2026-06-11 — Preserve hidden legacy categories referenced by history

### Context

The visible `r_ConfigurationData` block reflects current category structure, but historical transactions and allocations can still reference older hidden categories that no longer appear in that visible block.

### Decision

Keep `r_ConfigurationData` authoritative for visible group membership and ordering, but reconcile post-parse references from transactions and allocations against category metadata. Canonicalize simple reference variants and synthesize hidden inactive categories under an importer-owned hidden group when historical references still exist outside the visible configuration block.

### Consequence

dojo preserves visible sheet structure from `r_ConfigurationData` while still importing historical ledger rows that refer to older hidden categories. This avoids hard failures on live history without reopening broad header- or workbook-wide inference.

## 2026-06-11 — Treat zero-dollar allocations as no-op rows

### Context

The live Aspire allocation vectors include at least one zero-dollar row that is structurally present in the named ranges but does not represent real budget movement.

### Decision

Skip zero-dollar allocation rows during import while continuing to reject negative or malformed allocation amounts.

### Consequence

No-op allocation artifacts no longer block live imports, and dojo still rejects allocation rows that would change balances ambiguously or incorrectly.

## 2026-06-12 — Validate aggregates with a structured parity report

### Context

The original MVP import validation compared only a coarse fixture snapshot. That was enough to smoke-test the first import pass, but not enough to audit every aggregate value shown in the UI or to diagnose disagreements precisely.

### Decision

Add a first-class aggregate validation harness that compares source-sheet-derived expectations against persisted dojo aggregates and emits structured checks with labels, entity identity, month, source references, expected values, actual values, cent deltas, pass/fail state, and notes.

### Consequence

Aggregate correctness becomes directly testable in backend automation, import diagnostics, and developer reruns against fixture or saved real-sheet fetch dumps. Validation failures now point to a specific aggregate instead of a broad snapshot mismatch.

## 2026-06-12 — Derive budget-account net worth from the ledger, not duplicated imported valuation rows

### Context

Aspire net-worth reporting can contain duplicated valuation rows for budget accounts that are already represented in the transaction ledger. Counting those rows directly would double-count or override dojo's native account-balance source of truth.

### Decision

Compute budget-account net worth from imported budget-account balances in the ledger. Preserve imported valuation rows for those same budget accounts only as diagnostic items flagged `ignored_import_value = true`, and exclude them from the current net-worth total.

### Consequence

dojo's current net worth stays native and non-duplicative, while developers can still inspect the imported Aspire valuation rows during validation and UI review.

## 2026-06-12 — Hidden entities must not affect default visible aggregate totals

### Context

The budget UI showed visible-only category rows, but one of the summary aggregates still counted hidden-category spending. That made the displayed totals internally inconsistent.

### Decision

Treat hidden-account and hidden-category visibility as part of aggregate correctness. Any visible-only aggregate surface must exclude hidden entities unless the UI explicitly toggles them on.

### Consequence

Budget summaries, account lists, and other default visible totals now align with the entities currently shown on screen, reducing the risk of misleading aggregate numbers.

## 2026-06-12 — Match Aspire ATB semantics exactly, including starting-balance treatment

### Context

The real workbook exposes the ATB source directly: `Dashboard!J3` renders `Calculations!B59`. dojo's earlier ATB shortcut summed signed ATB and starting-balance transactions plus ATB allocations, which incorrectly subtracted liability starting-balance outflows.

### Decision

Match Aspire's ATB formula semantics exactly. Count ATB inflows and outflows, starting-balance inflows only, balance-adjustment inflows and outflows on budget accounts, and transfers into and out of the ATB bucket.

### Consequence

ATB now matches the source sheet on the deterministic fixture and on the saved live-sheet dump, and credit-card starting debt no longer incorrectly reduces the displayed amount available to budget.

The backend default budget month also now follows the current calendar month, matching Aspire's dashboard behavior instead of anchoring itself to the latest imported ledger row.

## 2026-06-12 — Use normalized duplicate detection for net-worth snapshots and fail ambiguous matches

### Context

Some imported net-worth snapshot categories refer to budget accounts with exact names, while others may differ only by emoji, spacing, punctuation, or case. Exact-name matching alone misses legitimate duplicates, but aggressive silent matching can also create false positives.

### Decision

Detect budget-account versus net-worth-snapshot duplicates in two stages: exact match first, then normalized-name match that strips decorative characters and compares case-insensitively. If exactly one budget account matches, treat the imported valuation as a duplicate diagnostic row and exclude it from native net worth. If multiple budget accounts match the same normalized snapshot name, mark it as an ambiguous duplicate, ignore it in the native total, and fail validation.

### Consequence

dojo avoids silent double-counting while still catching duplicate reporting that is not byte-for-byte identical. Ambiguous cases now become explicit validation failures instead of hidden inflation in the net-worth total.

## 2026-06-12 — Pass pre-computed categories to `list_category_groups` to eliminate double computation

### Context

`get_budget` called `list_categories` for budget data, then called `list_category_groups` which called `list_categories` again internally. This doubled all per-category work (transaction sum aggregation, allocation bucket aggregation, credit-card payment calculation).

### Decision

Add an optional `precomputed_categories` parameter to `list_category_groups`. When `get_budget` has already computed categories, it passes them directly instead of letting `list_category_groups` recompute them.

### Consequence

Eliminates the double-call overhead. No change to the public API. The `list_category_groups` method signature is extended but backward-compatible (defaults to computing categories if none provided).

## 2026-06-12 — Batch INSERT transactions and allocations during import

### Context

`_insert_bundle` called `insert_version` once per row, each generating a UUID and issuing a separate INSERT statement. For 10K transactions, this meant 10K individual INSERTs plus allocation INSERTs inside a single DuckDB transaction. Pytest profiling showed this was the dominant import cost (~42s for 10K).

### Decision

Add `batch_insert_versions` that pre-generates UUID row_ids and issues multi-row VALUES INSERTs in batches of 500 rows. Apply this to the two bulk entity types: transactions and allocations. Keep individual inserts for small entity tables (accounts, categories, groups).

### Consequence

10K import improved from ~42.5s to ~29.3s (1.45x). The approach keeps SCD2 validity semantics intact because all rows in a batch share the same `valid_from`/`valid_to` timestamps. For larger datasets, further gains would require COPY FROM or removing per-row UUID generation.

## 2026-06-12 — Slim bootstrap endpoint by removing the full `get_budget` call

### Context

The `GET /api/bootstrap` endpoint called `get_budget` which did all budget computation (transaction aggregation, allocation bucketing, ATB calculation) — but the frontend's `initialize()` immediately called `refreshBudget()` afterwards, which called `get_budget` a second time. Every field from bootstrap's budget response was overwritten within milliseconds. The bootstrap budget call was pure waste.

### Decision

Replace the `get_budget` call in `get_bootstrap` with direct SQL queries for entity records only (groups, categories) with zeroed-out budget fields. The `current_atb_minor` and `current_budget_month_summary` fields are set to zero defaults since they are overwritten by the subsequent `refreshBudget()` call. The bootstrap response is still returned (the frontend uses it as an initialization sentinel).

### Consequence

Bootstrap latency dropped from ~225ms to ~99ms on 10K datasets. Payload size reduced significantly (budget fields are zeroed, not computed). The frontend sees exactly the same user experience because `state.bootstrap` is checked only for truthiness, and the remaining fields (accounts, categories, groups) are immediately overwritten by parallel refresh calls.

## 2026-06-12 — Frontend paginated transaction loading

### Context

The transaction page loaded up to `limit=2000` transactions into client memory on every load/refresh. With the server-side pagination API already in place, the frontend was still consuming the full bounded response.

### Decision

Add `fetchTransactionsPage` to the API client with offset/limit parameters. Replace the single-page `refreshTransactions` with a paginated version that fetches page 0 (200 rows) and stores total/has_more metadata. Add `loadMoreTransactions` that appends the next page. Add a "Load More" button to the transaction view.

### Consequence

Initial transaction load is bounded to 200 rows (~8KB) instead of 2000 rows (~80KB+). Large ledgers are loaded incrementally as the user requests more. The client-side transaction array still grows, but only on demand.

## 2026-06-12 — Replace the user-facing `Carried over` label with `Starting Available`

### Context

The category-level formula itself was correct, but the `Carried over` label was not clear to users and the top-level budget summary displayed an aggregate that Aspire does not show in a directly reconcilable way.

### Decision

Keep the underlying prior-month-available formula, but present it as `Starting Available` on category and group tables. Remove the top-level budget summary metric for that value instead of showing an unexplained carryforward total.

### Consequence

Every displayed budget aggregate is now more directly reconcilable to either Aspire or dojo's own month formula: `available = starting available + budgeted + activity` for standard categories.
