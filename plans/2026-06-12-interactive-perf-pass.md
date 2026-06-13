# Complete Interactive And Import Performance Pass

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds.

## Purpose / Big Picture

The first benchmark pass proved aggregate correctness and exposed the remaining performance work that still affects real usage. This pass finishes the interactive transaction-table path, removes avoidable repeated budget aggregation work, reduces import latency with measured batch-oriented changes, and trims bootstrap so it stops acting like a full-app data dump.

After this work, a user with a realistic or synthetic large ledger should be able to open the transactions page without downloading or rendering the full ledger, keep scrolling or paging without DOM flooding, import a 10K-row workbook in a tolerable amount of time, and still get the same validated financial results that currently pass the 210-check aggregate harness.

The implementation must stay measurement-driven: benchmark or test the current path first, change only the proven bottlenecks, then re-measure and re-run aggregate validation.

## Progress

- [x] 2026-06-12 23:38Z — Reviewed benchmark report, prior performance plan, transaction API, frontend transaction state/table path, bootstrap endpoint, budget aggregation path, importer, SCD helpers, and benchmark/test commands.
- [x] 2026-06-12 23:38Z — Updated this ExecPlan to match the actual current codebase instead of the earlier partial plan.
- [x] 2026-06-12 23:57Z — Added transaction-window, budget-shaping, bootstrap-size, and import-phase benchmark coverage plus frontend/API regression tests for bounded paging and bounded DOM rendering.
- [x] 2026-06-12 23:57Z — Implemented bounded frontend transaction paging: initial load now requests `limit=100`, keeps only one page in reactive state, and uses previous/next page controls while preserving virtualized DOM rendering.
- [x] 2026-06-12 23:57Z — Proved transaction request bounds, payload size, state bounds, DOM bounds, and server-driven ordering with benchmark output and frontend/API tests.
- [x] 2026-06-12 23:57Z — Re-benchmarked the budget/category/group endpoints and removed the remaining repeated category computation from `GET /api/categories`.
- [x] 2026-06-12 23:57Z — Profiled import phases end-to-end on 1K and 10K synthetic datasets and recorded DB-write vs post-import snapshot costs.
- [x] 2026-06-12 23:57Z — Batched the remaining full-import dimension-table writes and reduced the 10K synthetic import profile to about 9.5s while preserving existing validation/test coverage.
- [x] 2026-06-12 23:57Z — Slimmed bootstrap to an app-shell payload and added a payload-size regression test.
- [x] 2026-06-12 23:57Z — Updated `ARCHITECTURE.md`, `SPEC.md`, `DECISIONS.md`, and `CHANGELOG.md` to match the final behavior and performance policy.
- [x] 2026-06-12 23:57Z — Ran lint, typecheck, tests, docs, container, benchmarks, and aggregate validation; all requested checks passed.

## Surprises & Discoveries

- Observation: The biggest bootstrap payload cost was not reference entities alone; it was the nested import validation report carried through `get_import_status()` into both bootstrap and app-status responses.
  Evidence: shrinking bootstrap to `app_status`, `import_status`, and `default_budget_month`, while stripping `validation_report`, dropped the fixture route payload from about 248,619 bytes to about 2,296 bytes.

- Observation: Once transaction and allocation batching existed, row-wise inserts for the smaller import tables were still surprisingly expensive relative to their row counts.
  Evidence: the first import profile showed ~1.8s spread across category-group, account, category, bucket, and setting writes before those tables were batched.

- Observation: DOM rendering is already windowed with a small custom virtual scroller, so the remaining interactive risk is primarily over-fetching and unbounded client-held rows, not thousands of mounted DOM nodes.
  Evidence: `web/src/dojo/components/VirtualDataTable.vue` slices to `visibleItems` based on viewport height and overscan.

- Observation: The backend transaction API supports only sort parameters today; there is no general transaction filter API to safely support arbitrary client-side filtering without accidental full-ledger fetches.
  Evidence: `api/src/dojo/api/routes.py` exposes `limit`, `offset`, `show_hidden`, `sort_by`, and `sort_dir` only.

- Observation: `get_budget()` already passes precomputed categories into `list_category_groups()`, so the original double-call bug was partially addressed, but the remaining measured overhead still needs fresh verification and possibly related endpoint cleanup.
  Evidence: `api/src/dojo/service.py:get_budget()` calls `self.list_category_groups(..., precomputed_categories=categories)`.

- Observation: After dimension-table batching, the remaining 10K synthetic import bottlenecks are transaction writes and post-import aggregate snapshot work, not row preparation.
  Evidence: the final 10K profile is about 9.5s total, with ~5.0s in `write_transactions_ms` and ~3.9s in `post_import_snapshot_ms`, while all other phases are small.

- Observation: The frontend did not need bootstrap-fetched accounts, categories, groups, or recent transactions because the ready path already follows bootstrap with dedicated budget/accounts/transactions/net-worth fetches.
  Evidence: `initialize()` now works correctly with a shell-sized bootstrap and the ready-state tests still pass.

## Decision Log

- Decision: Treat this pass as a continuation and correction of the earlier performance work rather than assuming the older plan still describes reality.
  Rationale: Several items in the prior plan are already partly implemented; repeating them blindly would create speculative churn and incorrect reporting.
  Date/Author: 2026-06-12 / agent

- Decision: Keep the existing custom `VirtualDataTable` unless measurement shows it is insufficient.
  Rationale: The current code already has a focused windowing implementation that bounds DOM rows. The open issue is request/state discipline, not an obvious need for a broader virtualization dependency.
  Date/Author: 2026-06-12 / agent

## Outcomes & Retrospective

The pass finished the four requested performance areas without adding product features or changing validated financial semantics.

- The interactive transaction-table path is now intentionally bounded end to end: backend page API, frontend `limit=100` requests, one page in reactive state, and existing virtual DOM rendering.
- The remaining budget double-computation was removed from `GET /api/categories` by shaping grouped and flat results from the same precomputed category list.
- The import path is now profiled by phase and batches all initial-load table writes. The local synthetic 10K import profile reached about 9.5s, which meets the stated tolerable ceiling but still leaves transaction writes and post-import aggregate snapshot work as the next bottlenecks.
- Bootstrap is now shell-sized and no longer ships the last validation report or large reference arrays during startup.

Remaining risk: the 10K import result is close to the tolerable ceiling rather than the desired target, and the synthetic import profile uses the post-import snapshot path as its large-scale aggregate-validation proxy because the synthetic benchmark fixture does not currently satisfy the full fixture-validation report assumptions.

Deferred exploration areas for the next import-performance pass:

- Replace transaction-row `VALUES` batching with a more DuckDB-native bulk load path such as a temp staging table plus `INSERT ... SELECT`, or another measured bulk-ingest primitive.
- Profile the real full aggregate-validation path separately from the synthetic post-import snapshot proxy so the next pass can target the actual validation ceiling directly.
- Push more month/category aggregate work into fewer grouped SQL passes inside validation and snapshot code, since post-import aggregate recomputation is now the second-largest import phase after transaction writes.
- Re-check workbook fetch/load and parse costs against a real local Aspire workbook path if available, because the current synthetic import profile isolates persistence and aggregate work more than remote workbook overhead.
- If bulk load and validation-path optimization still do not get close to the desired `<5s` target, consider a documented initial-load fast path that preserves SCD2 semantics while deferring only non-essential recomputation, but only after measurement justifies that additional complexity.

## Context and Orientation

Relevant repository paths and current responsibilities:

- `api/src/dojo/service.py` contains the main service layer, including `get_bootstrap()`, `get_budget()`, `list_transactions()`, import application, and validation snapshot helpers.
- `api/src/dojo/api/routes.py` exposes the FastAPI endpoints. `GET /api/transactions` already supports `offset`, `limit`, `sort_by`, `sort_dir`, and `show_hidden`.
- `api/src/dojo/scd.py` contains `insert_version()` and `batch_insert_versions()`, which define the current SCD2 write strategy.
- `api/src/dojo/importer.py` parses workbook named ranges into `ParsedImportBundle` domain data.
- `api/src/dojo/benchmarks.py` and `api/tests/test_benchmarks.py` provide the current synthetic-dataset benchmark harness.
- `web/src/dojo/state/app.ts` holds global frontend state and the current transaction pagination logic.
- `web/src/dojo/api/client.ts` builds API requests, including the paginated transaction request.
- `web/src/dojo/components/VirtualDataTable.vue` and `web/src/dojo/components/VirtualTransactionTable.vue` provide DOM windowing for the transaction list.
- `web/src/dojo/pages/TransactionsPage.vue` is the user-facing transaction table page.

Current transaction-table behavior:

- Initial load requests a page of 100 transactions from `/api/transactions`.
- Page navigation replaces `state.transactions` with the requested page instead of appending.
- DOM rows are windowed by `VirtualDataTable`, so only visible rows plus overscan mount.
- Sorting is server-side only insofar as the client hardcodes `sort_by=date&sort_dir=desc`; the UI does not expose alternate sorts yet.
- General filtering is not implemented in the transaction API or UI, so any future filtering behavior must remain bounded and must not reintroduce full-ledger fetches.

Current import behavior:

- `import_sheet_data()` parses or loads a `ParsedImportBundle`, clears domain tables, inserts the bundle, validates the resulting state against the imported bundle, and records the import batch.
- `_insert_bundle()` now batches every table used by the initial full-load import path, including the formerly row-wise dimension tables.
- Import profiling is available through `api/src/dojo/benchmarks.py` and `api/tests/test_benchmarks.py`, including phase timings for bundle build, table clearing, batched writes, and post-import aggregate snapshot work.

Current bootstrap behavior:

- Bootstrap returns `app_status`, `import_status`, and `default_budget_month` only.
- The frontend uses bootstrap to detect readiness and seed the selected month, then fetches budget, accounts, transactions, and net worth on demand.

## Plan of Work

First, extend measurement to the exact paths the user called out. The transaction-table work needs explicit proof of request bounds, payload size, reactive-state growth, and DOM node count, not just backend route timings. I will add backend and frontend checks that show how many rows are requested and rendered on initial load, and whether subsequent scrolling or paging keeps both request size and DOM size bounded.

Second, I will finish the transaction-table path with the smallest architecture change that fits the current Vue app. Because the existing table already virtualizes DOM rows, the most likely fix is to stop treating the accumulated fetched rows as the canonical full client dataset. The preferred outcome is a bounded client window or page model with server-driven sorting and any supported filters also expressed in the API request. If the current custom virtual scroller cannot support the desired scroll behavior cleanly, only then will I introduce a small focused dependency.

Third, I will re-benchmark the budget/category/group endpoints and confirm whether any repeated aggregation work remains in `get_budget()` or adjacent list endpoints. If measurements show no remaining material double-computation, I will keep the current readable structure and only update benchmarks/docs. If there is still repeated work, I will refactor shared aggregate shaping once and keep the response code explicit.

Fourth, I will profile the import path into coarse phases: parse/load, normalization, entity mapping, transaction/allocation/value preparation, write execution, and validation. Only after identifying the slow phases will I change `_insert_bundle()` or related helpers. The first optimization choices should be simple and batch-oriented: pre-resolve IDs once, reduce repeated lookups, batch small entity tables where that measurably matters, and avoid unnecessary SQL execution churn.

Fifth, I will measure bootstrap payload size and remove any response fields that are not required for initial shell render or immediate post-bootstrap routing. If recent transactions are only needed to derive the default month, I may replace them with a lighter dedicated field if that is the smallest correct change.

Finally, I will rerun correctness and developer verification, then sync docs and changelog with the actual measured results and residual risks.

## Concrete Steps

Run from the repository root inside the direnv-loaded Nix environment.

Baseline and profiling commands:

```bash
direnv exec . just bench-api-quick
direnv exec . just bench-api-routes
direnv exec . just test-api
direnv exec . just test-web
direnv exec . just validate-aggregates-fixture
```

Targeted implementation verification during the pass:

```bash
direnv exec . just test-api
direnv exec . just test-web
direnv exec . just bench-api
```

Final validation set:

```bash
direnv exec . just lint
direnv exec . just typecheck
direnv exec . just test
direnv exec . just docs
direnv exec . just container
direnv exec . just validate-aggregates-fixture
```

Success criteria:

- transaction-page initial load issues a bounded `/api/transactions` request with a small page/window size
- transaction-page DOM row count remains bounded even for large datasets
- transaction sorting/filtering semantics are explicit and do not require accidental full-ledger fetches
- benchmark output shows before/after timings and payload sizes for transaction, budget, bootstrap, and import paths
- aggregate validation remains fully green

## Validation and Acceptance

The change is accepted only if all of the following are true:

- The frontend transaction page no longer depends on fetching or storing the full ledger for initial render.
- A frontend test proves the initial transaction request uses a bounded limit and that rendered transaction row elements remain bounded.
- Backend/API tests prove paginated transaction responses preserve ordering semantics and bounded page metadata.
- Benchmark output reports the transaction-table initial page size, initial payload size, and relevant endpoint timings before and after the changes.
- Budget endpoint benchmarks show whether `get_budget`, category listing, and group listing improved or were confirmed already optimal enough after the earlier refactor.
- Import benchmark output reports total time plus phase timings for at least 1K and 10K synthetic datasets, and optionally a larger synthetic run if practical.
- Import regression coverage proves the optimized path preserves imported records, SCD2 validity behavior, ATB, balances, category availability, credit-card behavior, hidden-entity handling, and net-worth derivation.
- Bootstrap benchmarking reports payload bytes and guards against silent growth into a table-shaped dump.
- `direnv exec . just validate-aggregates-fixture` still passes all 210 checks.

Any new tests should fail before the corresponding change and pass afterward.

## Idempotence and Recovery

- Benchmark runs are repeatable and should not mutate checked-in files beyond planned test/doc updates.
- Synthetic benchmark datasets are generated in memory and can be rerun safely.
- Import optimizations must preserve SCD2 row-history semantics; if a batched write strategy changes persisted field values or intervals, revert that specific write-path change before proceeding.
- No step in this plan should delete source files, docs, lockfiles, or user data outside the normal test temporary directories.

## Interfaces and Dependencies

- Backend transaction API: `GET /api/transactions`
- Backend bootstrap API: `GET /api/bootstrap`
- Backend budget API: `GET /api/budget`, `GET /api/categories`
- Backend import path: `DojoService.import_sheet_data()`, `_apply_import_bundle()`, `_insert_bundle()`
- SCD helpers: `api/src/dojo/scd.py`
- Frontend transaction state: `web/src/dojo/state/app.ts`
- Frontend transaction UI: `web/src/dojo/pages/TransactionsPage.vue`, `web/src/dojo/components/VirtualTransactionTable.vue`, `web/src/dojo/components/VirtualDataTable.vue`
- Benchmark harness: `api/src/dojo/benchmarks.py`, `api/tests/test_benchmarks.py`
- Frontend tests: `web/tests/`

No new product feature surface should be introduced. Any new dependency must be narrowly justified by measured frontend rendering needs.

## Artifacts and Notes

Implementation evidence snapshot:

- `refreshTransactions()` now loads 100 rows on initial fetch and page navigation swaps the current page.
- `VirtualDataTable` still computes visible rows with `slice(startIndex, endIndex)` and default overscan of 6.
- `GET /api/bootstrap` fixture payload is now about 2.3 KB instead of about 249 KB.
- The final synthetic 10K import profile is about 9.5s total with ~5.0s transaction writes and ~3.9s post-import snapshot work.
