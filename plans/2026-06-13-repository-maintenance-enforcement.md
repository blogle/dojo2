# Implement Repository Maintenance Enforcement

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds.

## Purpose / Big Picture

The repository already contains a working local-first budgeting MVP, but many important engineering rules are still enforced only by habit. After this change, contributors should be able to use one canonical command surface, provision a fresh database deterministically, understand the repository from `README.md` and `CONTRIBUTING.md`, and rely on mechanical backend guardrails for architecture boundaries, direct DuckDB usage, persisted money types, direct wall-clock usage, and unsafe SQL patterns.

The first observable milestone is that `just check` and `just architecture-check` become meaningful repository gates instead of informal expectations. The second milestone is that backend tests can provision a fresh DuckDB database and freeze time explicitly without hidden schema work during import or FastAPI app construction.

## Progress

- [x] 2026-06-13 00:00Z - Inspected root documentation, `justfile`, Nix/direnv config, CI workflow, backend entrypoints, DB/schema code, major service methods, current tests, frontend package/test config, and benchmark files.
- [x] 2026-06-13 00:00Z - Recorded the initial repository inventory and concrete enforcement gaps in this ExecPlan.
- [x] 2026-06-13 13:05Z - Added explicit database provisioning and central clock infrastructure, then updated tests and startup flows to use them.
- [x] 2026-06-13 13:05Z - Added canonical `just` targets and aligned CI to them.
- [x] 2026-06-13 13:05Z - Added focused architecture and policy checks with representative self-tests.
- [x] 2026-06-13 13:05Z - Added reusable SCD2 invariant helpers plus stronger deterministic integration/property tests.
- [x] 2026-06-13 13:05Z - Moved the highest-value core SQL into native `.sql` files behind one loader and added SQL policy checks.
- [x] 2026-06-13 13:05Z - Updated repository documentation to match the implemented system and command surface.
- [x] 2026-06-13 13:05Z - Ran canonical validation commands and recorded the completed and deferred enforcement work.

## Surprises & Discoveries

- Observation: The repository is no longer a skeleton, but `README.md`, `SPEC.md`, and `AGENTS.md` still partially describe a bootstrap phase.
  Evidence: `README.md` line 48 says CI runs only lint, typecheck, test, and container; `SPEC.md` still names bootstrap skeleton goals even though the codebase already includes budgeting, import, transactions, categories, and net-worth logic.

- Observation: Schema bootstrap and migration execution currently happen inside `Database.__init__`, which means any service construction performs hidden persistent-state work.
  Evidence: `api/src/dojo/database.py` lines 37-41 call `duckdb.connect`, `bootstrap_sql()`, and `_run_schema_migrations()` unconditionally.

- Observation: There is no checked-in migration module or migration directory yet; the schema lives as Python string-returning functions.
  Evidence: `api/src/dojo/schema.py` exposes `bootstrap_sql()` and `migrate_sql()`; no `api/src/dojo/migrations/` directory or `.sql` migration files exist.

- Observation: The backend already uses SCD2-style `valid_from` and `valid_to`, but there are no reusable invariant helpers and no property tests over generated operation sequences.
  Evidence: `api/tests/test_scd.py` contains example tests only; `api/tests/test_properties.py` uses arithmetic identities instead of exercising repository behavior.

- Observation: The codebase already avoids direct `duckdb.connect(...)` in most production paths.
  Evidence: current search found production use only in `api/src/dojo/database.py`; the only other call is `api/tests/test_scd.py` for migration testing.

- Observation: The codebase already has one obvious wall-clock rule violation in domain code and one in SCD helpers.
  Evidence: `api/src/dojo/service.py` line 130 uses `date.today()`, and `api/src/dojo/scd.py` line 13 uses `datetime.now(timezone.utc)`.

- Observation: There is no current SQL loader and almost all backend SQL remains inline in Python.
  Evidence: no `.sql` files were found under the repository, and `api/src/dojo/service.py` contains most core read queries inline.

- Observation: Routers currently respect the database boundary reasonably well.
  Evidence: `api/src/dojo/api/routes.py` imports `DojoService` and request models, but does not import `duckdb` or call `duckdb.connect`.

- Observation: The repository has no Cypress configuration or e2e harness yet.
  Evidence: repository glob for Cypress files returned no matches, and `web/package.json` has no Cypress scripts or dependencies.

- Observation: Benchmark infrastructure already exists and should be preserved rather than rebuilt.
  Evidence: `api/src/dojo/benchmarks.py`, `api/src/dojo/benchmark_fixtures.py`, and `api/tests/test_benchmarks.py` provide deterministic synthetic datasets and timing reports.

- Observation: Transaction pagination is already implemented with backend bounds and frontend bounded state.
  Evidence: `api/src/dojo/service.py` lines 728-810 paginate results, and `web/src/dojo/state/app.ts` lines 127-145 keep only one page in reactive state.

- Observation: Persisted monetary fields already use integer minor units in the current schema.
  Evidence: `api/src/dojo/schema.py` uses `amount_minor BIGINT`, `target_amount_minor BIGINT`, and no persisted float monetary columns were found in the current schema source.

- Observation: The frontend lint configuration enforced Vue formatting rules that conflicted with the repository's Prettier output.
  Evidence: `just check` failed after `pnpm format:check` passed; the fix was to disable the remaining Vue formatting-only ESLint rules in `web/eslint.config.js`.

- Observation: Explicit provisioning and `:memory:` databases cannot be split across separate DuckDB connections.
  Evidence: `provision_database(":memory:")` provisions one transient connection, so benchmark helpers and direct SCD tests had to apply migrations on the same in-memory `Database.connection` that the service later used.

## Decision Log

- Decision: Start by enforcing the repository rules that can be made deterministic with the smallest changes to the existing code: explicit provisioning, central clock injection, canonical commands, and AST-backed policy tests.
  Rationale: Those changes reduce hidden behavior and create a stable foundation for later SCD2, SQL, and CI enforcement without a broad rewrite.
  Date/Author: 2026-06-13 / OpenCode

- Decision: Preserve the current application shape and add focused checks rather than introducing a general-purpose policy framework.
  Rationale: The prompt explicitly prefers small, explicit enforcement mechanisms over custom frameworks.
  Date/Author: 2026-06-13 / OpenCode

## Outcomes & Retrospective

The repository now has explicit DuckDB provisioning, a central backend clock, native SQL resources for schema and key query paths, deterministic migration and history tests, and focused AST-backed repository policy checks. `just check` and `just ci` both pass, and GitHub Actions now delegates to the canonical `just ci` command instead of re-encoding the checks in workflow YAML.

The main deferred area is browser end-to-end coverage. The command surface now reserves `just test-e2e` and reports the missing Cypress harness explicitly, but the repository still does not contain the dedicated Cypress server/database/time-control infrastructure requested by the prompt.

## Context and Orientation

The repository root contains the authoritative developer docs: `README.md`, `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md`, and `AGENTS.md`. `api/` contains the FastAPI backend and tests, and `web/` contains the Vue 3 frontend and tests. `justfile` is already the top-level command entrypoint, but its target set is incomplete for the current codebase and CI still reassembles check logic in workflow YAML.

The backend centers on `api/src/dojo/service.py`, which currently contains most query logic, business calculations, and write paths. `api/src/dojo/database.py` wraps a single DuckDB connection behind a process-level lock, but it also performs hidden schema bootstrap and migration work during object construction. `api/src/dojo/schema.py` stores schema and legacy transaction migration SQL as Python string factories instead of migration files. `api/src/dojo/scd.py` provides SCD2 helpers and query predicates, but it still owns a direct wall-clock function.

The current automated coverage is uneven. There are integration-style API tests, importer tests, SCD example tests, aggregate tests, web unit tests, and benchmark tests. There is no architecture test area yet, no checked-in Cypress harness, and the existing property tests do not validate repository behavior; they only assert simple arithmetic identities.

Initial repository inventory:

Existing compliant patterns to preserve:
- `api/src/dojo/database.py` already centralizes DuckDB connection ownership and serializes access with an `RLock`.
- `api/src/dojo/scd.py` already models current rows with `valid_to = MAX_TS` and exposes an `as_of_predicate()` helper.
- `api/tests/conftest.py` already uses temporary DuckDB files instead of a shared developer database.
- `api/tests/test_api_endpoints.py` and `web/tests/TransactionPagination.test.ts` already protect bounded transaction reads.
- `api/src/dojo/benchmark_fixtures.py` and `api/tests/test_benchmarks.py` already provide deterministic synthetic benchmark inputs.

Missing enforcement:
- No canonical `CONTRIBUTING.md`.
- No `just check`, `just ci`, `just architecture-check`, or migration provisioning command surface.
- No architecture/policy test area.
- No central clock abstraction.
- No AST-based prohibition for direct `duckdb.connect`, wall-clock calls, or unsafe SQL construction.
- No SQL loader or native `.sql` files.
- No migration provisioning test from zero.
- No reusable SCD2 invariant assertion helpers.
- No meaningful property tests for actual domain behavior.
- No Cypress/e2e system.

Rules currently enforced only by convention:
- Routers not importing `duckdb`.
- Routers not loading SQL directly.
- Production code opening DuckDB only through `Database`.
- Domain logic using integer minor units.
- Developers using `just` instead of invoking tool-specific commands.

Duplicate or conflicting documentation:
- `SPEC.md` describes a bootstrap skeleton rather than the implemented budgeting MVP.
- `README.md` and `ARCHITECTURE.md` are more current than `SPEC.md`.
- Root files `bootstrap_spec.md` and `mvp_spec.md` likely overlap historical scope and should be checked for conflict before any doc references point at them.

Tests depending on wall-clock time or mutable shared state:
- `service.default_budget_month()` uses `date.today()`, so any test relying on default month is date-sensitive.
- Current service fixtures create independent temp databases, which is good, but there is no shared frozen clock fixture yet.

SQL that is embedded, interpolated, or dynamically concatenated:
- `api/src/dojo/service.py` contains most inline SQL, including interpolated transaction paging SQL and table-name interpolation for destructive import clearing.
- `api/src/dojo/scd.py` builds SQL with f-strings for table and column names.
- `api/src/dojo/schema.py` embeds all schema SQL in Python strings.

Architectural boundary status:
- No current router-to-duckdb violation found.
- Domain service does not import FastAPI request/response classes.
- There is no mechanical guardrail preventing future violations.

SCD2 inconsistencies and gaps:
- Core tables follow the `valid_from`/`valid_to` pattern, but some editable tables also use domain-level `is_active` flags. Those flags are not redundant current-version flags, but they need to be documented clearly as domain activity state rather than SCD2 current-state markers.
- There are no deterministic overlap or single-current invariant checks across all SCD2 tables.

Financial invariant test gaps:
- No property tests for transfers, net worth preservation, transaction edit/void history, or import equivalence.
- Existing `api/tests/test_properties.py` does not touch repository code.

CI divergence:
- `.github/workflows/ci.yml` runs `just lint`, `just typecheck`, `just test`, and `nix build .#container`, but it does not run docs, architecture checks, or any explicit migration check command.
- CI logic is partially duplicated in YAML instead of fully routed through canonical `just` targets.

## Plan of Work

First, make hidden lifecycle behavior explicit. I will add an explicit migration/provisioning path, move schema application out of `Database.__init__`, add a central clock module, and thread explicit time into service write paths and tests. That gives the repository deterministic database state and deterministic time before policy checks are added.

Second, normalize the command surface and documentation. I will expand `justfile` so the repository exposes a clear local/CI interface, then update `.github/workflows/ci.yml` to call those targets rather than restating command logic. In parallel, I will create `CONTRIBUTING.md`, shorten `AGENTS.md`, and update the root docs to reflect the implemented architecture instead of the old bootstrap narrative.

Third, add policy enforcement as explicit tests and small helper modules. The check set will cover direct DuckDB connections, restricted wall-clock calls, router restrictions, persisted money type rules, and core SQL construction patterns. Each check will produce actionable file-and-line failures and will have at least one representative self-test against sample source snippets.

Fourth, strengthen stateful backend correctness. I will add reusable SCD2 invariant helpers, move the current trivial property tests toward actual repository behaviors, and add deterministic database fixtures that start from zero, apply migrations, and freeze time.

Fifth, move the most important read-path SQL into native `.sql` files behind a single loader, then document how to extend the enforcement without creating a generic framework. If a listed requirement cannot be implemented reliably in this pass, I will add the strongest partial guardrail and record the exact remaining gap.

## Concrete Steps

Run from the repository root inside the Nix dev shell loaded by direnv.

1. Inspect and update the execution plan while implementing.
   Expected result: this file reflects current progress, findings, and decisions.

2. Add explicit provisioning and clock support, then run narrow backend tests.
   Commands:
   - `just test-unit`
   - `just migration-check`

3. Add architecture and policy checks, then run the dedicated guardrail suite.
   Commands:
   - `just architecture-check`

4. Update canonical commands and CI wiring.
   Commands:
   - `just check`

5. Update docs and build them.
   Commands:
   - `just docs`

6. Run the full canonical completion suite that is feasible in this repository state.
   Commands:
   - `just ci`
   - `just container`

## Validation and Acceptance

The implementation is acceptable only if the repository proves the following through deterministic commands or tests:

- constructing a fresh test database from zero succeeds through an explicit provisioning path
- importing `dojo.api.main` and constructing the app no longer runs hidden migrations
- `just check` and `just ci` provide clear, non-zero-failing canonical quality gates
- `just architecture-check` fails on representative policy violations in dedicated checker tests
- direct `duckdb.connect(...)`, direct wall-clock calls, and prohibited SQL patterns are detected with file and line output
- SCD2 helper assertions can prove current, as-of, edit, and void invariants on real DuckDB state
- documentation points contributors to the exact commands and files that define repository behavior

If Cypress or other large missing systems cannot be implemented reliably in this pass, the final report must state that explicitly and identify the strongest partial guardrail implemented instead.

## Idempotence and Recovery

This work should be repeatable. Temporary test databases will live under pytest `tmp_path` or explicit temp directories and can be recreated safely. Root documentation edits are regular source changes. Migration/provisioning changes must avoid destructive shell commands and must not delete user data outside temporary test artifacts.

If a migration/provisioning step fails during development, the intended recovery path is to delete only the temporary test database and rerun the provisioning command. No step should require wiping the repository worktree.

## Interfaces and Dependencies

Expected interfaces after the change:

- `justfile` exposes canonical developer and CI targets
- `api/src/dojo/database.py` owns connection lifecycle only
- `api/src/dojo/migrations.py` or equivalent explicit provisioning entrypoint applies the current schema/migrations
- `api/src/dojo/clock.py` or equivalent clock abstraction provides system and test clocks
- `api/tests/architecture/` contains deterministic repository policy tests
- `api/tests/` contains reusable SCD2 invariant helpers and deterministic DB fixtures
- `.github/workflows/ci.yml` calls canonical `just` targets
- `CONTRIBUTING.md` becomes the authoritative developer workflow guide

## Artifacts and Notes

Initial high-priority gaps to close first:
- hidden schema work in `api/src/dojo/database.py`
- direct wall-clock calls in `api/src/dojo/service.py` and `api/src/dojo/scd.py`
- missing canonical contributor guide
- missing architecture/policy enforcement tests
- missing explicit migration/provisioning command
- no current Cypress/e2e foundation
