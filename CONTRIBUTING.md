# Contributing

`CONTRIBUTING.md` is the canonical development guide for this repository. It defines the required environment, the canonical commands, the repository layout, the deterministic test model, and where repository rules are enforced.

## Development Environment

- Use Nix and direnv.
- Run `direnv allow` from the repository root.
- Run `just setup` after entering the dev shell.
- Do not rely on host-installed Python, Node, `uv`, `pnpm`, DuckDB, `just`, or `mdbook`.

The repository keeps native tooling in `flake.nix` and language dependencies in `api/` and `web/`.

## Canonical Commands

Use the root `justfile` as the only routine command interface.

| Command | Purpose |
| --- | --- |
| `just setup` | Sync backend and frontend dependencies |
| `just dev` | Print the canonical local run commands |
| `just api` | Provision the API database and start FastAPI |
| `just web` | Start the Vue development server |
| `just build` | Build backend and frontend artifacts |
| `just format` | Apply formatting fixes |
| `just format-check` | Verify formatting without changing files |
| `just lint` | Run backend and frontend linters |
| `just typecheck` | Run Python and TypeScript type checking |
| `just architecture-check` | Run repository architecture and policy checks |
| `just migration-check` | Provision a fresh DuckDB database and verify schema startup rules |
| `just test-unit` | Run backend unit tests |
| `just test-property` | Run backend Hypothesis property tests |
| `just test-integration` | Run backend integration tests with real DuckDB |
| `just test-web` | Run frontend unit/component tests |
| `just test-e2e` | Reserved e2e entrypoint; currently reports the missing Cypress gap explicitly |
| `just test` | Run the normal backend and frontend test suites |
| `just bench` | Run backend and frontend benchmark commands |
| `just docs` | Build the mdBook documentation |
| `just check` | Run the normal pre-completion local quality gate |
| `just ci` | Run the canonical CI command |
| `just container` | Build the Nix container image |

## Narrow Versus Complete Checks

Use narrow commands while iterating:

- backend unit logic: `just test-unit`
- backend policy changes: `just architecture-check`
- schema/provisioning changes: `just migration-check`
- frontend work: `just test-web`, `just typecheck`, `just lint`

Before finishing a change, run `just check`. For CI-equivalent verification, run `just ci`.

## Repository Structure

- `api/src/dojo/`: backend application code
- `api/src/dojo/api/`: FastAPI entrypoints, request models, and routers
- `api/src/dojo/sql/`: native SQL resources
- `api/tests/`: backend tests, including architecture checks and support helpers
- `web/src/dojo/`: Vue application code
- `web/tests/`: frontend tests
- `docs/`: mdBook user documentation
- `agents/`: compact repository guidance and templates
- `plans/`: task-scoped ExecPlans for non-trivial implementation work

## Database Provisioning And Migrations

The repository uses explicit provisioning.

- Schema creation lives in `api/src/dojo/sql/schema/current.sql`.
- The provisioning entrypoint is `api/src/dojo/migrations.py`.
- `just api` runs `python -m dojo.migrations` before starting FastAPI.
- `api/src/dojo/database.py` owns connection lifecycle only. It must not run schema bootstrap or migrations as a side effect of object construction.

### Add Or Update A Migration

This repository is pre-v1 and currently provisions the current schema directly instead of maintaining a long chain of checked-in historical migration files.

When changing persistent schema:

1. Update `api/src/dojo/sql/schema/current.sql`.
2. If an explicit compatibility repair is required for an existing local database shape, add it under `api/src/dojo/sql/schema/migrations/` and invoke it from `api/src/dojo/migrations.py`.
3. Update or add tests in `api/tests/test_migrations.py`.
4. Run `just migration-check`.
5. Update `ARCHITECTURE.md` and `CHANGELOG.md`.

## SQL Rules

Core SQL belongs in native `.sql` files under `api/src/dojo/sql/`.

- Schema SQL goes under `api/src/dojo/sql/schema/`.
- Reusable query SQL goes under `api/src/dojo/sql/queries/`.
- Load SQL through `api/src/dojo/sql.py` using `load_sql()` or `render_sql()`.
- Only render dynamic SQL fragments from explicit allowlists in Python code.
- Do not interpolate request input into SQL identifiers, ORDER BY expressions, or WHERE fragments.
- Routers must not load SQL resources directly.

Small inline SQL is still acceptable when it is local and non-domain-specific, such as `BEGIN`, `COMMIT`, `ROLLBACK`, or a focused single-row lookup used only inside a test.

## Time Handling

Backend domain and persistence code must use the central clock abstraction in `api/src/dojo/clock.py`.

- Production code uses `SystemClock`.
- Tests use a deterministic test clock from `api/tests/support/clock.py`.
- Direct calls such as `datetime.now`, `datetime.utcnow`, or `date.today` are prohibited outside approved clock infrastructure and test-only code.

## Deterministic Test State

Backend integration and property tests use real DuckDB with explicit provisioning and frozen time.

- `api/tests/conftest.py` provisions a temporary DuckDB database for each test.
- `api/tests/support/clock.py` provides a mutable deterministic clock.
- `api/tests/support/scd_invariants.py` provides reusable SCD2 history assertions.
- `fixture://default` is the canonical sanitized import fixture used by automated tests.

Tests must not depend on:

- a developer's local `.duckdb` file
- wall-clock time
- execution order
- checked-in mutable state under `data/`
- network access unless the test is explicitly exercising the live Google harness outside normal CI usage

## Adding Or Updating Tests

Use the smallest deterministic test that enforces the rule.

- Unit tests: isolated parsing, validation, helpers, and small domain functions
- Property tests: money movement, transfers, SCD2 history changes, and generated operation sequences
- Integration tests: real DuckDB provisioning plus service/API behavior
- Architecture tests: AST-backed repository policy enforcement under `api/tests/architecture/`
- Web tests: frontend component and state behavior under `web/tests/`

When adding a new repository rule, prefer:

1. database constraint
2. type rule
3. existing linter configuration
4. small architecture/policy test
5. focused unit or integration test
6. documentation only if no mechanical enforcement is practical

## Architecture And Policy Checks

Repository policy checks live under `api/tests/architecture/`.

Current enforced checks cover:

- direct `duckdb.connect(...)` usage outside approved infrastructure and tests
- direct wall-clock calls outside approved clock infrastructure and tests
- router imports of `duckdb` or SQL loader helpers
- router financial arithmetic heuristics
- large inline SQL and SQL f-strings in service/router code
- SQL resource location under approved directories
- production imports of test-only modules
- persisted money columns using non-integer minor-unit types or float types

Run them with `just architecture-check`.

### Add A New Enforcement Check

1. Add a focused checker to `api/tests/architecture/checkers.py` or a nearby small helper.
2. Add one test that proves the checker catches a representative violation.
3. Add or update the repository-wide policy test so the real codebase is scanned.
4. Wire the check through an existing canonical command, usually `just architecture-check`.
5. Document the rule here if a contributor needs procedural guidance in addition to the mechanical check.

Do not build a general-purpose enforcement framework. Keep checks small and explicit.

## SCD2 Rules

Editable financial and configuration records use SCD2 history.

- Current rows are identified by `valid_to = MAX_TS`.
- SCD2 tables store `row_id`, logical identifier, `valid_from`, `valid_to`, `created_at`, and `created_by_user_id`.
- Tests must preserve historical rows after edits and voids.
- Do not add `is_current` or `is_active` as a redundant current-version flag. Domain-level `is_active` is acceptable only when it represents business activity state, not SCD2 row currentness.

Use `api/tests/support/scd_invariants.py` when adding SCD2 behavior or tests.

## Documentation Update Triggers

- Update `README.md` when setup, run, or high-level repository orientation changes.
- Update `CONTRIBUTING.md` when workflow, command surface, or enforcement guidance changes.
- Update `SPEC.md` when current product behavior or acceptance criteria change.
- Update `ARCHITECTURE.md` when code structure, runtime behavior, persistence model, SQL organization, or test architecture change.
- Append to `DECISIONS.md` when a durable technical tradeoff or policy decision is made.
- Update `CHANGELOG.md` for meaningful user-visible or developer-significant changes.

## Document Ownership

| Document | Owns |
| --- | --- |
| `README.md` | project overview, stack, setup, run commands, top-level links |
| `CONTRIBUTING.md` | canonical development workflow |
| `SPEC.md` | current product behavior and acceptance criteria |
| `ARCHITECTURE.md` | current implementation structure and runtime model |
| `DECISIONS.md` | durable technical decisions and tradeoffs |
| `CHANGELOG.md` | meaningful changes over time |
| `AGENTS.md` | agent routing only |

## Skills And Agent Templates

The repository keeps agent-related artifacts under `agents/`.

- `agents/execplan.md` defines the ExecPlan format.
- `agents/create-skill-template.md` defines the minimum self-contained structure for a new skill or workflow template.

A new skill should only be added when it captures a recurring or error-prone workflow that is not already obvious from commands and docs.
