# Architecture

## Runtime Topology

dojo has two runtime applications:

- `api/src/dojo/api/main.py`: FastAPI application
- `web/src/dojo/`: Vue 3 frontend built with Vite

The backend persists application state in DuckDB. The frontend treats the backend as the system of record and fetches small bootstrap data first, then budget, transactions, accounts, categories, and net-worth data on demand.

## Domain Boundaries

- `api/src/dojo/api/`: HTTP entrypoints, request parsing, and app wiring
- `api/src/dojo/service.py`: domain operations, read shaping, and write paths
- `api/src/dojo/database.py`: connection lifecycle and serialized DuckDB access
- `api/src/dojo/migrations.py`: explicit schema provisioning
- `api/src/dojo/sql/`: native SQL resources
- `api/src/dojo/importer.py`: fixture and Google Sheet import parsing
- `api/src/dojo/aggregate_validation.py`: aggregate correctness checks against imported source data

Routers call `DojoService` through FastAPI request state. Routers do not own DuckDB connection creation or SQL loading.

## Request Flow

1. `just api` provisions the DuckDB schema by running `python -m dojo.migrations`.
2. FastAPI startup constructs one `DojoService` and stores it on `app.state`.
3. Route handlers in `api/src/dojo/api/routes.py` resolve the service from request state.
4. Service methods run queries and writes through `Database`, which serializes access with a process-level `RLock` around one DuckDB connection.
5. Responses are returned as JSON to the Vue frontend.

The backend intentionally does not run migrations as a side effect of Python import, `Database` construction, or FastAPI app construction.

## Database Access Model

- `api/src/dojo/database.py` owns the DuckDB connection.
- `api/src/dojo/migrations.py` applies the current schema explicitly.
- The current implementation uses one process-local connection protected by an `RLock`.
- There is no custom read/write lock and no claimed concurrent-read support yet.

## SCD2 Model

Editable tables use SCD2 history with:

- `row_id`
- a logical identifier such as `account_id`, `transaction_id`, or `category_id`
- `valid_from`
- `valid_to`
- `created_at`
- `created_by_user_id`

Current rows are identified by `valid_to = MAX_TS`. Historical queries use `valid_from <= as_of < valid_to`.

The schema does not use `is_current` flags. Existing `is_active` fields on accounts and categories are domain attributes describing business activity state, not SCD2 current-row markers.

## Current And Historical Query Model

- `api/src/dojo/sql/schema/current.sql` defines `current_*` views for current-state reads.
- `api/src/dojo/scd.py` provides `current_predicate()` and `as_of_predicate()` helpers for explicit historical filtering.
- `api/tests/support/scd_invariants.py` contains reusable assertions for non-overlap, single-current, no-current, and history preservation after edits and voids.

## SQL Organization

- `api/src/dojo/sql/schema/`: schema and compatibility-repair SQL
- `api/src/dojo/sql/queries/`: reusable query and insert SQL
- `api/src/dojo/sql.py`: SQL loader helpers

Core read-path SQL such as account listing, transaction paging, account balances, current-view reads, import-run inserts, and Available to Budget transaction selection now lives in `.sql` files.

## Central Time Handling

- `api/src/dojo/clock.py` defines `SystemClock` and `FrozenClock`.
- `DojoService` receives a clock and uses it for version timestamps and business date selection.
- Backend tests use `api/tests/support/clock.py` for deterministic mutable time.

## Deterministic Testing Architecture

- `api/tests/conftest.py` provisions a fresh temporary DuckDB database for each test.
- `api/tests/test_migrations.py` proves that the current schema provisions a fresh database and that importing `dojo.api.main` does not create or migrate the database as a side effect.
- `api/tests/architecture/` contains repository policy checks for direct DuckDB usage, wall-clock usage, router boundaries, SQL patterns, SQL file location, and persisted money types.
- `api/tests/test_properties.py` uses Hypothesis against real repository behavior for allocations, transfers, status changes, and transaction history.
- `web/tests/` covers frontend state and component behavior.

There is currently no checked-in deterministic Cypress harness. `just test-e2e` is reserved and reports that gap explicitly.

## Import Architecture

The importer is named-range-first and allowlist-driven.

- `fixture://default` is the canonical deterministic source used by automated tests.
- Google Sheet imports fetch only the consumed named ranges.
- The importer parses accounts, category groups, categories, transactions, allocations, and net-worth valuations into the DuckDB ledger.
- `api/src/dojo/aggregate_validation.py` compares persisted aggregates against the interpreted imported source data and records structured pass/fail results.

## Performance-Sensitive Paths

The most performance-sensitive backend paths are:

- transaction paging
- category aggregate shaping
- budget shaping
- full import writes and post-import validation

`api/src/dojo/benchmarks.py` and `api/tests/test_benchmarks.py` provide deterministic synthetic benchmarks for these paths.

## Persisted Derived State And Caches

The repository currently persists import bookkeeping in `import_runs` and `import_batches`.

It does not currently persist authoritative financial summary cache tables. Budget totals, account balances, and net-worth rollups are derived from current ledger tables at read time.
