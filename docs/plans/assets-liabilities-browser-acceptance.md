# Automate Assets & Liabilities browser acceptance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as implementation proceeds.

## Purpose / Big Picture

Assets & Liabilities currently requires repeated manual browser walkthroughs to establish that rich financial workflows remain correct. After this plan is complete, `just test-e2e` will start the real Vue application and FastAPI API against an isolated deterministic DuckDB database, exercise seven agreed user workflows in Chromium, and report both correctness and performance evidence.

The suite is intentionally small. It proves the integration seams and user-visible financial outcomes that unit, property, integration, and component tests cannot prove together. New browser scenarios are added only when product use reveals a meaningful regression risk.

## Progress

- [x] (2026-08-20) Agreed on the E2E architecture, fixture boundaries, selector policy, performance policy, and initial seven scenarios.
- [x] (2026-08-20) Committed the prerequisite rich-account remediation as `24e1b1e`.
- [x] (2026-08-20) Implemented the deterministic scenario builder, E2E-only reset boundary, Chromium orchestration, metrics collection, and AL-01.
- [x] (2026-08-20) Implemented AL-02 tangible asset creation and verified persistence across detail, reload, overview, and net worth.
- [ ] Implement and commit AL-03 independently.
- [ ] Implement and commit AL-04 independently.
- [ ] Implement and commit AL-05 independently.
- [ ] Implement and commit AL-06 independently.
- [ ] Implement and commit AL-07 independently.
- [ ] Establish initial performance budgets from representative measurements and complete the broad repository quality gate.

## Surprises & Discoveries

- Observation: `fixture://default` is useful for importer and budget tests but is not a sufficient rich-account acceptance seed.
  Evidence: `api/src/dojo/fixture_data.py` contains budget accounts, categories, transactions, allocations, and two imported tracking accounts, but no investment account, tangible asset, rich loan, statement, account-budget link, or cutover state.

- Observation: Cypress component tests do not exercise the deployed integration path.
  Evidence: `web/cypress/component/AccountDetailPage.cy.ts` and `web/cypress/component/AddItemWizardPage.cy.ts` mount pages with reduced routers and mocked `window.fetch` implementations.

- Observation: Electron is unstable for the larger component specs in the current environment while Chromium is stable.
  Evidence: `plans/2026-06-17-implement-product-spec/VALIDATION.md` records Electron `SIGSEGV` failures; a full Chrome component run on 2026-08-20 passed 265 tests in 37 specs.

- Observation: A generated AL-01 DuckDB baseline is 7.51 MiB and takes about 0.5 seconds to rebuild.
  Evidence: Two clean consecutive harness runs measured 518–538 ms baseline generation, 846–848 ms API startup, 562–564 ms web startup, 85–91 ms reset, and 1.88–1.93 seconds Cypress suite time.

- Observation: dojo2 has no dedicated Net Worth browser route.
  Evidence: `web/src/dojo/router.ts` exposes budgets, transactions, Assets & Liabilities, creation, and account detail routes. AL-01 therefore verifies the independent real `/api/net-worth` read rather than inventing an unapproved page.

- Observation: Fingerprint-keyed XDG baseline reuse keeps multi-scenario setup bounded.
  Evidence: The first two-scenario build generated 11.52 MiB in 1.17 seconds; the next run reused both baselines and completed baseline validation in 271 ms.

## Decision Log

- Decision: Use the real Vue application, FastAPI process, and DuckDB persistence boundary for acceptance behavior.
  Rationale: Browser acceptance must prove routing, request serialization, API validation, persistence, cache invalidation, and cross-page rendering together.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Setup data bypasses ordinary product APIs unless the setup workflow itself is under test.
  Rationale: Recreating prerequisites through HTTP makes tests slow and obscures failures. The action under acceptance still traverses the real browser-to-API path.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Use a temporary file-backed DuckDB owned by the API process, not a cross-process in-memory database.
  Rationale: Cypress Node and FastAPI are separate processes. DuckDB in-memory databases are connection-local, and two processes must not write the same live DuckDB file.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Reset state through an E2E-only API control endpoint.
  Rationale: The API owns the open DuckDB connection. A reset endpoint available only under explicit E2E configuration can safely close, restore, and reopen the service without exposing destructive behavior in development or production.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Compose each fixture from shared core SQL plus a scenario-specific SQL delta.
  Rationale: One large golden fixture hides prerequisites, while fully independent fixtures duplicate foundational records. Core plus delta keeps each scenario explicit without scattering SQL through Python.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Keep canonical fixture SQL under `api/src/dojo/sql/tests/e2e/` and load it through `load_sql`.
  Rationale: This follows the repository's existing SQL resource and architecture-check conventions. Python and Cypress contain no inline SQL.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Measure generated DuckDB size and generation cost before choosing cache-only or checked-in baselines.
  Rationale: File size alone does not justify a binary fixture. Generation time, DuckDB compatibility, reviewability, and CI behavior must be measured first.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Generated caches and run artifacts use `${XDG_CACHE_HOME:-$HOME/.cache}/dojo/e2e/`.
  Rationale: Disposable generated data does not belong in a repository `.local/` directory. If baselines are later versioned, they will use the explicit path `api/tests/fixtures/e2e/databases/`.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Record timings on every E2E run, but do not begin with tight wall-clock failure thresholds.
  Rationale: Environment-sensitive timing gates are themselves flaky. Representative measurements establish generous initial budgets, and later changes may only lower those budgets without an explicit reviewed decision.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Land each acceptance scenario in a separate sequential commit.
  Rationale: Each scenario remains independently reviewable, measurable, and reversible. Infrastructure work may proceed in parallel in non-overlapping files, but integration and commits remain serialized.
  Date/Author: 2026-08-20 / product owner and opencode

- Decision: Keep generated baseline databases in the XDG cache rather than checking them into Git.
  Rationale: AL-01 alone is 7.51 MiB while deterministic regeneration costs about 0.5 seconds. Seven checked-in binaries would add substantial opaque repository weight for negligible runtime savings.
  Date/Author: 2026-08-20 / opencode

- Decision: AL-01 uses the existing `/api/net-worth` response as the independent net-worth surface.
  Rationale: No dedicated Net Worth page exists, and adding one without an approved product or visual contract would expand scope. The real browser still proves overview and detail behavior while `cy.request` proves the independently shaped net-worth read.
  Date/Author: 2026-08-20 / opencode

## Outcomes & Retrospective

The first two scenarios are working end to end. AL-01 starts real API and Vite processes, resets an API-owned worker database, verifies grouped values and detail routing in Chromium, and independently verifies net worth. AL-02 creates a tangible asset through the real wizard, reloads its generated detail route, and verifies overview and net-worth persistence. The accumulated suite has two tests, uses 44 browser API requests, and completes Cypress execution in 3.89 seconds with cached baselines. AL-03 through AL-07 remain.

The first three-run profile recorded medians of 524 ms baseline generation, 847 ms API startup, 582 ms web startup, 75.19 ms reset, and 1,901 ms Cypress suite time. The corresponding p95 values were 527 ms, 848 ms, 589 ms, 81.74 ms, and 1,914 ms. These are observations, not failure thresholds; timing budgets remain deferred until the seven-scenario suite has representative CI evidence.

## Context and Orientation

The FastAPI application is created in `api/src/dojo/api/main.py`. Its lifespan creates one `DojoService`, and `DojoService` owns one `Database` connection for the process lifetime. `api/src/dojo/migrations.py` provisions the schema explicitly before service startup. The E2E reset implementation must respect that ownership: Cypress must never open or replace the active database directly.

The Vue application starts in `web/src/main.ts`, installs the production router from `web/src/dojo/router.ts`, and calls backend initialization from `web/src/dojo/App.vue`. Cypress E2E tests must visit this real application rather than mounting pages directly.

The root `justfile` is the canonical command interface. `just test-e2e` is currently a placeholder. This plan replaces it with deterministic orchestration that starts an API process without reload, starts Vite on a fixed worker-specific port, waits for both services, runs Cypress in Nix-provided Chromium, and cleans up processes reliably.

An acceptance scenario is one coherent user behavior with explicit preconditions and observable outcomes. A scenario fixture is a database state used only to establish those preconditions. The scenario action and its resulting reads use the real browser and product API.

## Fixture and Reset Contract

Scenario SQL lives under `api/src/dojo/sql/tests/e2e/`. `core.sql` creates common ready-application records such as an import batch, budget account, category group, standard categories, buckets, allocations, and stable logical identifiers. Files under `api/src/dojo/sql/tests/e2e/scenarios/` add only the records required by one acceptance scenario.

Fixture SQL is data-only. It does not create tables, views, constraints, or sequences. Schema provisioning remains the responsibility of `api/src/dojo/migrations.py`. Every amount uses integer minor units. IDs, UTC timestamps, effective dates, transaction entry order, and financial event order are explicit. Python maps an allowlisted scenario name to fixed SQL resources and never interpolates browser-controlled SQL or paths.

Each scenario has a backend fixture-contract test. The test provisions a fresh database, loads core plus the delta, starts `DojoService` with the fixed E2E clock, and proves the headline values required by the browser scenario. This catches fixture drift before Cypress starts.

The reset endpoint is registered only when `APP_ENV=e2e` and a reset token is configured. It accepts an allowlisted scenario key, not a path. It restores a closed baseline into a worker-specific database, recreates `DojoService` with the fixed clock, clears process-local OAuth state, and returns the scenario, fixture fingerprint, fixed time, database size, restore duration, and service reopen duration. The route does not exist in normal development or production.

Cypress resets the selected scenario in a suite-level `beforeEach` before visiting the application. Browser test isolation clears cookies and browser storage; the reset clears server and database state. No test depends on another test's mutation.

## Selector and Synchronization Contract

Selectors express stable user behavior. Pages, meaningful regions, actions, modals, and repeated entity rows expose kebab-case `data-cy` hooks. Repeated rows expose a stable row hook and are located by their user-visible identity within the correct region. Critical values have dedicated hooks scoped to their entity or metric.

Tests do not use implementation CSS classes, DOM ancestry, child indexes, `.first()`, `.last()`, `.eq()`, unscoped text searches, generated UUID values, or broad whole-page text assertions. Visible labels may be asserted when the wording is itself product behavior, but ambiguous elements are located through feature-specific hooks.

Tests synchronize on visible ready states and aliased network requests. Fixed `cy.wait(...)` sleeps are prohibited. Cypress retries are initially zero so instability remains visible rather than hidden. Animations are disabled, the viewport and browser are fixed, the browser and backend clocks use the same UTC instant, and no external network dependency is permitted.

Full-page pixel snapshots are not acceptance criteria. Existing fixture-driven component tests remain the appropriate layer for narrow visual states.

## Acceptance Scenarios

### AL-01: Truthful grouped overview and cross-surface totals

Given cash of $20,000, a $500,000 tracking asset, a $25,000 tangible asset, a $12,000 investment, a $200,000 loan principal liability, and a $4,000 restricted escrow asset, when the user opens Assets & Liabilities, then every entity appears in the correct group, total assets are $561,000, total liabilities are $200,000, and net worth is $361,000.

The independent `/api/net-worth` read reports the same $361,000. When the user selects a representative entity, the production router opens its detail page and the detail value agrees with the overview. This scenario is the broad application-wiring smoke test; later scenarios provide mutation coverage.

### AL-02: Tangible asset creation persists through the real wizard

Given a ready application with $20,000 net worth and the fixed business date, when the user opens Add item, chooses Tangible asset, enters a $25,000 opening valuation, and submits, then the browser navigates to the real detail route, the detail page reports $25,000, the entity appears under Tangible assets, and net worth becomes $45,000.

When the page is reloaded, the created entity and value remain visible. This proves production route precedence, request validation, DuckDB persistence, query invalidation, and aggregate inclusion.

### AL-03: Same-date tracking correction updates every surface

Given a tracking asset with a $500,000 snapshot on date D, when the user records a $510,000 snapshot for the same date D, then the detail page reports $510,000, snapshot history presents one effective result for D, the overview reports $510,000, and net worth increases by $10,000.

Reloading preserves the corrected result. Historical SCD2 revision rows remain backend integration-test responsibility and are not exposed as browser acceptance details.

### AL-04: Cash-only investment reconciliation is accepted

Given an investment account without a reconciled statement, when the user reconciles a statement containing $12,000 cash and no holdings, then the operation succeeds without requiring a blank holding row, the detail page reports $12,000, the overview reports the investment at $12,000, and net worth increases by $12,000.

The UI does not fabricate a holding, price, or reconciled value from absent data.

### AL-05: Investment contribution preserves provenance and net worth

Given Checking contains $20,000, Brokerage has a $10,000 same-day statement, Brokerage is linked to Investment Contributions, and that category has $1,500 available, when the user records a cleared $1,000 contribution from Checking to Brokerage, then Checking becomes $19,000 and Brokerage becomes provisionally $11,000.

Brokerage activity shows one semantic $1,000 contribution operation with date, direction, source account, destination account, status, and memo. The Transactions page contains both paired transfer ledger legs. The Investment Contributions category reports -$1,000 Activity, $500 available, and one derived -$1,000 row in Spending history. Net worth remains $30,000. The contribution is budget activity, not income or economic spending.

When the user records a later same-day statement that includes the contribution, Brokerage remains $11,000, the provisional adjustment is no longer applied separately, provenance remains visible, and net worth remains $30,000.

The category view intentionally shows one derived operation row rather than both ledger legs. Showing both as category spending would either double-count the contribution or visually sum to zero. The Transactions page remains the place to inspect both accounting legs.

### AL-06: Linked loan payment appears across transaction, budget, and loan views

Given a Mortgage category linked uniquely to Chase Mortgage, Chase Mortgage has $200,000 principal and $4,000 escrow, and Checking has sufficient funds, when the user records a cleared $5,000 mortgage payment from Checking, then the Transactions page shows the categorized Mortgage transaction, the Mortgage category reports -$5,000 monthly Activity, and the Mortgage drawer's Spending history shows that transaction.

Chase Mortgage's Payment activity shows the same transaction with its date, source account, amount, status, and memo. Payment entry does not ask for principal, interest, fee, or escrow splits.

When the user reconciles a later statement showing $198,000 principal and unchanged $4,000 escrow, then principal reduction is $2,000, unknown non-principal cost is $3,000, Assets & Liabilities shows a $198,000 loan liability and a separate $4,000 restricted asset, and projections remain labeled as estimates.

The bootstrap scenario assumes one uniquely linked loan. Follow-up interaction for multiple loans sharing one category is outside this initial suite.

### AL-07: One-to-many tracking cutover preserves signed net worth

Given a tracking asset contributes $500,000 to net worth and the fixed business date is the cutover date, when the user replaces it with a $200,000 investment asset, a $350,000 tangible asset, and a $50,000 loan liability, then the predecessor no longer appears in the current overview and all three successors appear in their correct groups.

Their combined signed contribution is $500,000, net worth is unchanged, and no ordinary transaction or allocation is created. Reloading does not restore the predecessor or duplicate successors. Day-before temporal resolution and retry idempotence remain backend integration-test responsibilities until the product exposes a browser historical mode.

## Performance Measurement and Ratchet

Every E2E run writes a machine-readable report under `${XDG_CACHE_HOME:-$HOME/.cache}/dojo/e2e/runs/` and prints a concise summary. CI uploads the report as an artifact. The report records browser and DuckDB versions, fixture fingerprint, generated baseline byte size, baseline generation duration, API startup duration, frontend startup duration, per-test restore duration, service reopen duration, per-test wall duration, request count, failed request count, and total suite duration.

`just test-e2e` runs the functional suite once. A separate canonical profiling recipe runs enough repetitions to calculate median and high-percentile phase durations without hiding functional failures. The first implementation records data only. After representative local and CI runs exist, a checked-in budget file at `web/cypress/e2e/performance-budgets.json` defines generous phase ceilings.

The comparison command fails only when a measured phase exceeds its reviewed ceiling or a deterministic structural budget is violated. Structural budgets include zero fixed sleeps, zero test retries, no external requests, one scenario reset per test, and no setup loops through product CRUD APIs. A normal performance improvement may lower a budget. Raising one requires an explicit commit explaining the regression or environmental change.

The suite must remain diagnosable. The report identifies the slowest setup phase and test. On failure, the E2E cache retains the worker database, API log, frontend log, Cypress screenshot, scenario fingerprint, and timing report. Successful runs may clean disposable worker databases while retaining the latest metrics.

## Plan of Work

First, implement the backend scenario builder and reset lifecycle. Add explicit E2E settings and clock construction without importing test modules into production modules. Keep the reset router separate from product routes and include it only in E2E mode. Add backend tests proving route absence outside E2E, token enforcement, scenario allowlisting, repeatable reset, complete service replacement, and metric reporting.

In parallel, add Nix-provided Chromium, Cypress E2E configuration, process orchestration, XDG cache paths, stable support commands, and result collection. Do not move component fixtures or add a second frontend mock server. Integrate this work with AL-01 so the first E2E commit demonstrates a useful browser behavior rather than landing an unused harness.

After AL-01 passes, add AL-02 through AL-07 in order. Each scenario commit contains its SQL delta, fixture-contract test, minimal stable hooks, Cypress behavior test, and any product correction the test reveals. Before each commit, run the scenario alone and the complete accumulated E2E suite. Do not batch multiple scenarios into one commit.

After all seven scenarios pass, collect representative timing runs, decide whether generated baseline databases remain XDG-cached or are checked into `api/tests/fixtures/e2e/databases/`, add initial reviewed budgets, update architecture and validation records, and run the broadest repository quality gate.

## Concrete Steps

Run commands from the repository root. The implementation must provide these canonical entrypoints:

    just test-e2e
    just test-e2e-spec <spec-path>
    just profile-e2e

Use the narrow scenario command before every scenario commit, then run `just test-e2e`. Run `just architecture-check`, `just migration-check`, `just lint`, and `just typecheck` whenever infrastructure or API boundaries change. Run `just check` before declaring the plan complete.

The commit sequence is:

    docs: define assets and liabilities browser acceptance
    test(e2e): accept truthful assets overview
    test(e2e): accept tangible asset creation
    test(e2e): accept tracking snapshot correction
    test(e2e): accept cash-only investment reconciliation
    test(e2e): accept investment contribution provenance
    test(e2e): accept linked loan payment activity
    test(e2e): accept tracking cutover

If formatting drift unrelated to this plan blocks `just check`, fix it in an isolated commit rather than mixing it into an acceptance scenario.

## Validation and Acceptance

The plan is complete when all seven scenarios pass independently and together in Nix-provided Chromium, every scenario starts from a deterministic reset, no test uses fixed sleeps or retries, no external network request occurs, and a failed scenario leaves sufficient artifacts to reproduce the state.

The same run must produce performance evidence identifying baseline generation, startup, reset, service reopen, individual scenario, request-count, and total-suite costs. Initial budgets must be based on observed results rather than guessed thresholds.

Existing backend unit, property, integration, migration, architecture, frontend unit, and Cypress component tests remain authoritative for their layers. Browser acceptance does not duplicate exhaustive domain arithmetic, SCD2 internals, migration permutations, loan projection formulas, or pixel-level visual comparisons.

## Idempotence and Recovery

Scenario generation and reset are safe to repeat. Every run uses worker-specific paths under the XDG cache and never touches the developer database. The reset endpoint accepts only known scenarios and cannot be enabled accidentally without explicit E2E environment and token configuration.

If orchestration fails, process cleanup must terminate only child processes started by that run. A failed run retains its worker directory for diagnosis. The next run creates a fresh worker path and does not depend on cleaning the failed state first.

If a checked-in baseline is later adopted, canonical SQL remains the source of truth and a regeneration/verification command must prove that the binary matches the current schema, fixture fingerprint, and DuckDB version.

## Artifacts and Notes

The rich-account implementation prerequisite is commit `24e1b1e`. Existing manual validation evidence is in `plans/2026-06-17-implement-product-spec/VALIDATION.md`. The broader feature plan is `docs/plans/complete-assets-liabilities.md`.

Generated E2E artifacts do not belong under a repository `.local/` directory or `/tmp/opencode`. The default external location is `${XDG_CACHE_HOME:-$HOME/.cache}/dojo/e2e/`.

## Interfaces and Dependencies

The implementation uses the repository's existing FastAPI, DuckDB, Vue, Cypress, and Nix dependencies. It must not add Cucumber or a second behavior-test framework. Markdown scenarios define acceptance; ordinary Cypress TypeScript implements them with matching scenario names.

The backend needs an explicit E2E configuration type or settings fields for the fixed clock, reset token, worker database path, and baseline directory. The reset controller accepts a typed scenario identifier and returns typed reset metrics. The scenario loader accepts only repository-defined scenario identifiers and SQL resource names.

Cypress support provides one command to reset a named scenario and a small set of selectors or helpers that encode stable user actions, not page implementation details. Process orchestration owns child-process startup, readiness checks, logs, cleanup, and metrics output. All routine commands remain routed through the root `justfile`.

Revision note: Created 2026-08-20 from the product-owner-approved acceptance discussion. Updated after AL-01 to record measured baseline costs, the XDG-cache decision, the absence of a Net Worth page, the API-based cross-surface assertion, and first complete-run performance evidence.
