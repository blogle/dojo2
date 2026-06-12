# Build First Dojo MVP Vertical Slice

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds.

## Purpose / Big Picture

Turn the current bootstrap skeleton into a runnable local-first envelope budgeting MVP backed by DuckDB, with a FastAPI API, a Vue 3 frontend, fixture-driven import validation, and versioned SCD2 domain state. After this change, a developer can start the app, import deterministic fixture data or a copied Google Sheet, land on a usable budget dashboard, manage accounts/categories/transactions/allocations, and inspect net worth summaries without relying on the original spreadsheet. The behavior is observable through the onboarding flow, the budget/accounts/transactions pages, and automated backend/frontend test coverage.

## Progress

- [x] 2026-06-10 00:00Z — Read `mvp_spec.md`, `AGENTS.md`, `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `README.md`, `CHANGELOG.md`, and `agents/execplan.md`.
- [x] 2026-06-10 00:10Z — Inspected the existing backend/frontend bootstrap structure and current toolchain files.
- [x] 2026-06-10 15:10Z — Implemented backend foundation: settings, DuckDB connection lifecycle, schema bootstrap, SCD2 helpers, readiness state, and budget query services.
- [x] 2026-06-10 15:45Z — Added importer/parser/validation stack with deterministic fixture harness, Google Sheets read-only path, and automated import golden tests.
- [x] 2026-06-10 16:00Z — Added API endpoints for bootstrap, onboarding, import, budget, allocations, transactions, transfers, accounts, categories, and net worth.
- [x] 2026-06-10 17:15Z — Implemented the Vue application shell, onboarding, budget, accounts, transactions, and management flows with earth-tone brutalist styling and virtualized transaction rendering.
- [x] 2026-06-10 17:20Z — Expanded automated coverage across backend unit/property/integration layers and frontend component/app tests.
- [x] 2026-06-10 17:25Z — Updated developer/user docs, env examples, and changelog to reflect the MVP.
- [x] 2026-06-10 17:32Z — Ran `just setup`, `just lint`, `just typecheck`, `just test`, `just docs`, and `just container`, fixing an in-scope `LD_LIBRARY_PATH` vs `nix build` issue.
- [x] 2026-06-10 22:07Z — Refactored the importer to use centralized named-range discovery/validation, updated importer tests and docs, and reran narrow plus broad validation commands.
- [x] 2026-06-11 11:11Z — Corrected the importer contract to support `COLUMN_VECTOR`, `TABLE_BLOCK`, and `SCALAR_OR_LABEL` shapes, updated fixtures/tests/docs, and reran narrow plus broad validation commands.
- [x] 2026-06-11 23:01Z — Re-read the current ExecPlan plus root docs, then traced the importer regression around category-group membership.
- [x] 2026-06-11 23:04Z — Replaced category/group derivation so `r_ConfigurationData` drives visible hierarchy and ordering while `UserDefCategories` remains metadata-only.
- [x] 2026-06-11 23:05Z — Added regression tests for `r_ConfigurationData` membership/order, scalar row-symbol parsing, ignored broken ranges, and name-agnostic parsing.
- [x] 2026-06-11 23:07Z — Updated importer docs/changelog, reran narrow importer tests, and reran `just lint`, `just typecheck`, `just test`, `just docs`, and `just container`.
- [x] 2026-06-11 23:18Z — Fixed live-sheet import failure caused by unnamed trailing category metadata rows and reran importer and broader test coverage.
- [x] 2026-06-11 23:24Z — Fixed live-sheet import failure caused by non-ISO sheet date strings and reran importer and broader test coverage.
- [x] 2026-06-11 23:46Z — Fixed transaction-row classification so amount-less structural/helper rows embedded in transaction vectors are skipped, added regression coverage, and reran narrow importer tests, backend tests, lint, and typecheck.
- [x] 2026-06-12 00:34Z — Added a live-sheet harness, iterated on real-sheet import failures, and reached a successful live import against the target Google Sheet.

## Surprises & Discoveries

- Observation: The repository currently contains only health/status endpoints and a single static frontend page.
  Evidence: `api/src/dojo/api/health.py`, `api/src/dojo/api/main.py`, and `web/src/dojo/components/StaticWelcome.vue` hold the only application behavior.

- Observation: DuckDB timestamp decoding required `pytz` in the Python environment during test execution.
  Evidence: early fixture-import tests failed with `ModuleNotFoundError: No module named 'pytz'` while reading `TIMESTAMPTZ` values from DuckDB.

- Observation: exporting `LD_LIBRARY_PATH` from the dev shell fixed DuckDB's native dependency loading, but it also broke `nix build .#container` until that variable was unset for the container recipe.
  Evidence: `just container` initially failed with `libstdc++.so.6: version 'CXXABI_1.3.15' not found`, then passed after changing the recipe to `env -u LD_LIBRARY_PATH nix build .#container`.

- Observation: the initial importer pass relied on header scanning, but the intended spreadsheet contract is materially stronger when expressed through named ranges discovered from sheet metadata.
  Evidence: follow-up implementation direction explicitly replaced header parsing with named-range discovery, validation, and zipped-column import semantics.

- Observation: the first named-range refactor still assumed every range was a single-column vector, which broke valid rectangular blocks such as `r_ConfigurationData`.
  Evidence: import failed with `Named range r_ConfigurationData is not a single-column range` until the importer contract was expanded to classify vectors, blocks, and scalar labels explicitly.

- Observation: after the shape-model fix, category hierarchy still came from `UserDefCategories` zipped with optional group-name vectors instead of the already-consumed `r_ConfigurationData` table block.
  Evidence: `api/src/dojo/importer.py` still built `parse_configuration_categories_and_groups()` from `config.category_names` plus `config.category_group_names`, while only tests validated `r_ConfigurationData` as a block.

- Observation: using `r_ConfigurationData` as the ordering source changes the default fixture category order because group rows and category rows are now read exactly in sheet display order.
  Evidence: importer tests needed to update expected category order from vector order to `Grocery`, `Secret Stash`, `Utilities`, then `Reserve Card Payment`.

- Observation: real-sheet category metadata vectors can contain trailing rows with values in amount or goal columns but no category name, which triggered a false validation failure before `r_ConfigurationData` parsing even ran.
  Evidence: live import raised `ValueError: Meaningful category row 36 is missing the category name` from `parse_configuration_categories_and_groups()` while scanning zipped metadata vectors.

- Observation: live Google Sheets values can arrive as display-formatted dates like `1/1/2021` rather than ISO `YYYY-MM-DD`, and the importer currently assumes ISO-only parsing for transactions, allocations, and net worth rows.
  Evidence: live import raised `ValueError: Invalid isoformat string: '1/1/2021'` from `parse_date_value()` during transaction parsing.

- Observation: Aspire transaction named ranges can contain non-transaction structural rows with date, status, account, category, or memo values but no inflow or outflow, and the importer currently treats any such nonblank row as a malformed transaction.
  Evidence: live import raised `ValueError: Meaningful transaction row 7 is missing inflow/outflow` from `parse_transactions_named_ranges()`.

- Observation: the live sheet also contains at least one pending staged transaction row with an amount and memo but no account or category, immediately following a structural separator row.
  Evidence: the live-sheet harness reproduced row `9100` as `{date: 07/10/2025, inflow: $2,346.80, account: '', category: '', memo: 'LION RENTAL A E (Sixt?)', status: pending_symbol}`.

- Observation: the live sheet contains at least one posted amount-bearing transaction row with a blank date that is intended to inherit the visible date from the previous transaction row.
  Evidence: the live-sheet harness reproduced row `9541` as an approved `ALO YOGA` outflow with blank date, immediately after row `9540` on `09/23/2025`.

- Observation: the live allocation vectors contain at least one zero-dollar row that is structurally present in the named ranges but does not represent real budget movement.
  Evidence: the live-sheet harness reproduced allocation row `524` as `12/31/2021, $0.00, Available to budget -> Travel`.

## Decision Log

- Decision: Build the MVP around a small repository-local service layer instead of introducing a larger ORM or generic event model.
  Rationale: The specification explicitly prefers simple, explicit code and domain-specific tables; direct DuckDB SQL keeps query formulas close to the spec.
  Date/Author: 2026-06-10 / OpenCode

- Decision: Implement import tests against a deterministic repository fixture while keeping the live Google Sheets OAuth and fetch path available behind environment configuration.
  Rationale: The repository does not include real spreadsheet credentials or an exported source workbook, but the spec requires a working validation harness and a manual path once credentials exist.
  Date/Author: 2026-06-10 / OpenCode

- Decision: Enable Tailwind build plumbing while keeping the actual visual system primarily expressed through project-owned CSS variables and components.
  Rationale: The MVP spec requires Tailwind in the frontend stack, but the brutalist financial visual language is more maintainable here as explicit component styling than as a large utility-class conversion pass.
  Date/Author: 2026-06-10 / OpenCode

- Decision: Refactor the importer so named ranges are the authoritative sheet interface and any header parsing is non-authoritative fallback-only.
  Rationale: named ranges are semantically stable across spreadsheet layout drift and allow one central validation layer for required fields, lengths, and row zipping.
  Date/Author: 2026-06-10 / OpenCode

- Decision: Keep named ranges authoritative, but make shape handling explicit with `COLUMN_VECTOR`, `TABLE_BLOCK`, and `SCALAR_OR_LABEL` contract entries.
  Rationale: Aspire uses row-zipped ledger vectors, rectangular configuration/report blocks, and scalar constants; correct parsing requires shape-aware validation before any importer logic runs.
  Date/Author: 2026-06-11 / OpenCode

- Decision: Treat `r_ConfigurationData` as the sole source of visible category-group membership and display ordering, and use scalar named ranges to interpret its row symbols instead of hardcoded glyphs or fallback group-name vectors.
  Rationale: the flat `UserDefCategories` metadata vectors do not preserve group boundaries, while the rectangular configuration block does.
  Date/Author: 2026-06-11 / OpenCode

- Decision: Classify transaction-vector rows before validation and import only amount-bearing real transactions; skip break, reconciliation, blank, and other helper rows embedded in Aspire transaction vectors.
  Rationale: live Aspire sheets can place structural or UI rows inside the consumed transaction named ranges, but amount-bearing rows still need strict validation.
  Date/Author: 2026-06-11 / OpenCode

- Decision: Treat pending amount-bearing rows with both account and category blank as skipped staging/helper rows rather than imported transactions.
  Rationale: the live workbook contains this pattern as an incomplete staged sheet row, and importing it would either fail validation or invent missing account/category semantics.
  Date/Author: 2026-06-11 / OpenCode

- Decision: Allow a real amount-bearing transaction row with a blank date to inherit the most recent prior real transaction date.
  Rationale: the live workbook uses this sparse display pattern at least once, and the adjacent rows make the intended date unambiguous without weakening first-row validation.
  Date/Author: 2026-06-11 / OpenCode

- Decision: Skip zero-dollar allocation rows as no-op sheet artifacts while continuing to reject negative or malformed allocation amounts.
  Rationale: the live workbook includes at least one zero-value allocation row, and importing it would add no ledger information.
  Date/Author: 2026-06-11 / OpenCode

## Outcomes & Retrospective

The repository now contains a working first-draft budgeting app instead of a bootstrap shell. The backend owns a DuckDB SCD2 ledger, fixture/live import paths, parity validation, and the required CRUD/formula endpoints. The frontend now supports onboarding, budgeting, transaction entry and editing, transfer entry, account/category management, hidden-entity toggles, and a minimal net-worth view with virtualized transaction rendering.

The importer now uses named ranges as the authoritative spreadsheet contract. Discovery, required-range validation, shape-aware parsing, and row zipping are centralized in `api/src/dojo/importer.py`, and the Google fetch layer now reads named-range metadata and values rather than tab payloads.

The category/group correction is complete. Visible group membership and category ordering now come from `r_ConfigurationData` parsed as a table block with consumed scalar row symbols, while `UserDefCategories`, `UserDefAmounts`, `UserDefGoals`, and linked-account vectors remain metadata-only. Regression coverage now proves that obsolete group-name vectors are ignored for hierarchy, alternate category names still parse correctly, and unrelated broken ranges such as `trx_Uuids` stay ignored.

Live-sheet compatibility work is now in place as well. The importer tolerates padded category metadata rows, display-formatted dates, structural and staged transaction rows, sparse inherited transaction dates, zero-dollar allocation rows, uncategorized real transactions, and historical hidden category references that no longer appear in the visible configuration block. A repository-local harness at `api/src/dojo/live_sheet_harness.py` can fetch and import the allowlisted named ranges from a real Google Sheet into a temporary DuckDB file for tight iteration without mutating the main app database.

The broad repository workflows pass after adjusting the container recipe to unset `LD_LIBRARY_PATH` before `nix build`. The main remaining gap against the full MVP acceptance matrix is Cypress E2E coverage: backend and frontend automated coverage is in place, but browser-level end-to-end tests were not added in this pass. Live Google-sheet parity still depends on real credentials and a copied spreadsheet, though the code path and manual runtime flow are implemented.

## Context and Orientation

The repository is a two-app monorepo. The backend lives under `api/src/dojo/` and currently exposes only health/status endpoints. The frontend lives under `web/src/dojo/` and currently renders one static page that checks backend reachability. Developer workflows are rooted in `justfile`, with Python dependencies managed by `uv`, frontend dependencies by `pnpm`, and native tooling provided by `flake.nix`. The MVP spec in `mvp_spec.md` is the product source of truth and imposes several hard constraints: DuckDB is the canonical database, domain tables are SCD2 versioned with `valid_from`/`valid_to`, `TX_AVAILABLE_TO_BUDGET` and `BUCKET_AVAILABLE_TO_BUDGET` must be distinct, hidden entities must be preserved, transfers remain ordinary transactions, and credit-card behavior must be derived from transactions plus allocations rather than a hidden event ledger.

Relevant files at the start of work:

- `api/src/dojo/api/main.py` — current FastAPI app entrypoint.
- `api/src/dojo/api/settings.py` — environment-backed settings.
- `api/tests/` — currently only health/settings tests.
- `web/src/dojo/` — current Vue app shell and static landing page.
- `web/tests/App.test.ts` — current component smoke test.
- `ARCHITECTURE.md` and `README.md` — still describe the bootstrap skeleton and must be updated.

## Plan of Work

Start from the backend core so the app stays runnable throughout implementation. First, extend settings and add a small application state package under `api/src/dojo/` containing constants, typed models, DuckDB bootstrap SQL, connection management, SCD2 helper functions, and query services for current/as-of views plus budget formulas. Seed a minimal system group/bucket model and store app/import readiness state.

Next, add the import layer. Implement parsers that can read either a deterministic local fixture document or live Google Sheets named-range payloads, discover semantic named ranges centrally, parse money and statuses, map source system categories, create domain rows by zipping named-range columns, and run validation against expected fixture snapshots. Keep batch metadata only in `import_batches`, and implement a small validation report model so onboarding can present successes/failures.

Then expose the domain through API routers. Add endpoints required by the MVP: app/bootstrap/import/onboarding/budget/allocation/transaction/transfer/account/category/net-worth surfaces. Keep request/response models explicit, route handlers thin, and service logic in backend modules.

With the API in place, rebuild the frontend from the static page into a routed application shell. Add onboarding, budget, accounts, transactions, and settings/management screens using Vue 3 composables and focused components. Apply the earth-tone brutalist styling rules from the spec, add a lightweight virtual transaction table that only renders the visible window plus overscan, and ensure the UI supports the core workflows rather than decorative placeholder screens.

After the slices are working, deepen automated coverage: backend unit/property/integration tests for formulas and importer semantics, frontend component tests for money/category/transaction UI, and limited Cypress E2E coverage for onboarding and common budget flows. Finish by updating architecture and changelog docs, recording any durable tradeoffs in `DECISIONS.md`, and running the required `just` commands.

## Concrete Steps

Run all commands from the repository root inside the direnv-loaded Nix shell unless a subdirectory is explicitly stated.

1. Inspect and modify backend files under `api/src/dojo/`, then run narrow checks such as:

       cd api && uv run pytest tests/test_<area>.py

   Expected result: targeted backend tests exit 0.

2. After importer changes, run targeted API tests covering parsing, schema, and validation:

       cd api && uv run pytest tests/test_import_*.py tests/test_budget_*.py

   Expected result: fixture import plus formula tests exit 0.

3. After frontend component changes, run focused web tests:

       cd web && pnpm test -- --run <pattern>

   Expected result: changed component tests exit 0.

4. Before completion, run the required repository workflows:

       just setup
       just lint
       just typecheck
       just test
       just docs
       just container

   Expected result: commands exit 0, or any failure is documented with the exact cause and recovery path.

## Validation and Acceptance

The implementation is accepted when:

- Starting the backend exposes `GET /api/app/status`, `GET /api/bootstrap`, `GET /api/budget?month=YYYY-MM`, and the remaining MVP endpoints with typed JSON payloads.
- An empty database reports onboarding-required state; importing the deterministic fixture marks the app ready and produces non-empty budget, account, transaction, and net-worth data.
- Budget formulas match the fixture expectations for account balances, ATB, category balances, monthly activity/budgeted values, rollover, credit-card payment availability, and net-worth ignore behavior.
- Editing/deleting/toggling versioned entities preserves prior as-of results in automated tests.
- The Vue app allows fixture onboarding, category funding/moves/returns, transaction CRUD/status toggles, transfer entry, hidden-entity toggles, and account/category/group management, with transaction rows rendered through DOM-culling virtualization.
- The required test suites and `just` workflows pass, except for any explicitly documented environment-gated Google OAuth/manual validation steps.

## Idempotence and Recovery

Database bootstrap and fixture import should be repeatable against a fresh DuckDB file. Retry behavior for import failures should leave the app in not-ready state and allow a corrected re-import without destructive repository changes. File edits are ordinary source changes tracked by git; no destructive commands should be used. If the DuckDB file accumulates incompatible test data during development, it can be removed manually outside git because the schema and fixture import are reproducible from source.

## Interfaces and Dependencies

Expected backend interfaces:

- FastAPI app in `api/src/dojo/api/main.py`
- DuckDB schema/services under `api/src/dojo/`
- Required endpoints listed in `mvp_spec.md` Section 15
- Environment variables including `DUCKDB_PATH`, `DEV_FIXTURE_MODE`, `GOOGLE_OAUTH_*`, `SESSION_SECRET`, and frontend `VITE_API_BASE_URL`

Expected frontend interfaces:

- Routed Vue application under `web/src/dojo/`
- Fetch-based API client modules under `web/src/dojo/api/`
- Virtualized transaction rendering component under `web/src/dojo/components/`

Supporting dependencies likely required:

- Python: `duckdb`, `hypothesis`, and small HTTP/session helpers for OAuth flow
- Frontend: `pinia` only if simple composables become insufficient, plus a Vue-friendly virtual list utility and Cypress for E2E coverage

## Artifacts and Notes

- Source spec: `mvp_spec.md`
- Current bootstrap docs that will need updates: `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`
- This plan intentionally treats missing live Google credentials as an environment limitation, not as a reason to weaken fixture-based acceptance coverage.
