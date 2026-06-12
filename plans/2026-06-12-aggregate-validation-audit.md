# Audit Aggregate Correctness End To End

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as work proceeds.

## Purpose / Big Picture

Pause feature work and prove that every financial aggregate currently surfaced by dojo is correct. After this change, a developer can import the deterministic fixture or a real copied Aspire sheet, run a backend validation command/report, and verify that the account balances, category balances, month budget values, credit-card payment behavior, hidden-entity handling, Available to Budget, account totals, and net-worth totals shown by the API and Vue UI match dojo's native formulas and the source sheet where applicable. The output must identify disagreements precisely enough to trace them back to importer parsing, formula/query semantics, API serialization, or UI display.

## Progress

- [x] 2026-06-12 00:00Z — Re-read `AGENTS.md`, `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md`, `agents/execplan.md`, and `mvp_spec.md`.
- [x] 2026-06-12 00:10Z — Reviewed the existing MVP ExecPlan plus backend importer/service/schema/API/frontend aggregate display surfaces.
- [x] 2026-06-12 09:50Z — Added `api/src/dojo/aggregate_validation.py` and `api/src/dojo/validation_cli.py`, plus `just validate-aggregates-fixture` and `just validate-aggregates-dump` command paths.
- [x] 2026-06-12 09:58Z — Replaced the old coarse import parity snapshot with detailed structured aggregate checks including labels, entity/month identity, source references, cent deltas, and notes.
- [x] 2026-06-12 10:02Z — Added deterministic backend tests for aggregate validation reports, API aggregate values, hidden-entity behavior, and existing formula semantics.
- [x] 2026-06-12 10:05Z — Documented and enabled the real-sheet validation path through saved live-sheet fetch dumps produced by `dojo.live_sheet_harness`.
- [x] 2026-06-12 10:06Z — Added UI aggregate rendering tests and tightened budget/accounts/net-worth labels plus backend-provided group totals.
- [x] 2026-06-12 10:07Z — Investigated the first structural discrepancy, fixed hidden-category spending leaking into the default visible budget summary, and reran validation until the fixture report was clean.
- [x] 2026-06-12 10:08Z — Updated architecture/spec/decisions/changelog docs and ran `just lint`, `just typecheck`, `just test`, `just docs`, and `just container`.
- [x] 2026-06-12 10:20Z — Re-reviewed the plan/docs/code before follow-up edits, fetched live-sheet metadata, and identified the real Aspire ATB source cells as `Dashboard!J3` backed by `Calculations!B59`.
- [ ] Add failing tests and validation checks for the live-sheet ATB semantics, net-worth duplicate matching, and carried-over UI semantics.
- [ ] Correct ATB semantics to match `Calculations!B59`, including starting-balance and balance-adjustment handling.
- [ ] Add normalized duplicate detection for budget-account vs net-worth-snapshot identities and surface ambiguous matches as validation issues.
- [ ] Rename or remove the carried-over aggregate in the user-facing budget UI so every displayed value is reconciliable.
- [x] 2026-06-12 13:02Z — Added failing fixture/UI regressions for ATB semantics, normalized net-worth duplicates, ledger-row labeling, and the carried-over label.
- [x] 2026-06-12 13:10Z — Corrected ATB semantics, added normalized/ambiguous net-worth duplicate handling plus labeled ledger rows, and renamed the budget column to `Starting Available` while removing the top carryforward summary metric.
- [x] 2026-06-12 13:18Z — Optimized the aggregate validation report to compute actual category/group/month values in one pass from current DB tables so the saved live-sheet dump validates successfully.
- [x] 2026-06-12 13:27Z — Re-ran fixture validation, live-dump validation, and the required repository checks after the follow-up corrections.

## Surprises & Discoveries

- Observation: the current import validation path only compares a small fixture snapshot and does not emit source references, deltas, or per-aggregate diagnostics.
  Evidence: `DojoService._validate_bundle()` only compares top-level structures such as `account_balances`, `category_available`, `month_activity`, and `native_net_worth_minor` against `bundle.expected`.

- Observation: budget group panels currently display category rows only; they do not display or test group aggregate totals even though the audit requires validation for any aggregate totals shown.
  Evidence: `web/src/dojo/components/CategoryGroupPanel.vue` renders `group.categories.length` but no money totals.

- Observation: the net-worth page currently labels sources minimally and shows ignored imported budget-account valuations in the same table without a stronger distinction between displayed native totals and ignored imported duplicates.
  Evidence: `web/src/dojo/pages/NetWorthPage.vue` renders `source` and `ignored_import_value` columns but no explicit total label or validation metadata.

- Observation: the visible budget summary originally included hidden-category spending even though the category table itself excluded hidden rows by default.
  Evidence: the first aggregate validation report failed `budget.summary.spent` for `2026-01` with expected visible spending `15000` vs actual `19000`, caused by `DojoService.compute_spent()` ignoring the `show_hidden` filter.

- Observation: budget-account ledger net-worth items in the API use the account `name` field instead of `account_name`, while imported valuation items use `account_name`.
  Evidence: the first validation pass hit `StopIteration` when looking up ledger net-worth rows by `account_name`; `DojoService.get_net_worth()` appends raw account rows for `source = 'ledger'`.

- Observation: the real Aspire Available to Budget value is rendered on `Dashboard!J3` and comes from the unrounded formula cell `Calculations!B59 = SUM(B61,B62) - SUM(B63,B60)`.
  Evidence: a direct Google Sheets fetch returned `Dashboard!J3 = $0.00` and `Calculations!B59 = -0.000000006053596735`, with `B60/B61/B62/B63` expanding to ATB inflows/outflows, starting-balance inflows, balance adjustments, and category-transfer totals.

- Observation: dojo's ATB mismatch is not caused by the live sheet's current-month display alone; it comes from source-formula semantics around starting balances.
  Evidence: replaying the raw sheet formula against the fetched named ranges produces `0`, but replaying dojo's current imported formula semantics produces `-816904` cents because dojo includes outflow starting-balance rows in ATB while Aspire counts only starting-balance inflows.

- Observation: the real sheet's dashboard month is date-driven (`Dashboard!B2 = June 12, 2026`), while imported transactions and allocations currently stop in `2026-03`.
  Evidence: the live dump metadata shows `Dashboard!B2`, and parsing the imported named ranges shows latest transaction/allocation months of `2026-03`.

- Observation: the full live-dump validation command initially timed out because the report recomputed category aggregates through `DojoService.list_categories()` and `get_budget()` for every month and category.
  Evidence: `python -m dojo.validation_cli --fetch-dump /tmp/dojo-live-sheet-last-fetch.json` exceeded 120s before optimization, then completed with `failed_check_count = 0` after the report switched to one-pass DB-table derivations.

## Decision Log

- Decision: build a first-class backend aggregate validation report instead of extending the coarse import summary structure in place.
  Rationale: the audit needs labeled checks, source references, cents deltas, and explanatory notes that are useful both during import validation and as a standalone developer command.
  Date/Author: 2026-06-12 / OpenCode

- Decision: keep dojo-native formulas authoritative for budget-account net worth and use Aspire net-worth rows only as cross-check inputs for non-budget tracking values and duplicate-budget-entry diagnostics.
  Rationale: the source sheet duplicates some budget-account values in net-worth reporting; trusting those rows directly would double-count or override the ledger-derived source of truth.
  Date/Author: 2026-06-12 / OpenCode

- Decision: treat Aspire ATB semantics as authoritative for validation by matching `Calculations!B59`, which counts ATB inflows/outflows, starting-balance inflows only, balance adjustments, and allocation transfers into/out of ATB.
  Rationale: the live sheet exposes the exact formula, and dojo's prior signed-starting-balance shortcut is demonstrably wrong on real imported data.
  Date/Author: 2026-06-12 / OpenCode

- Decision: make the backend default budget month current-date-driven instead of latest-ledger-driven.
  Rationale: Aspire's dashboard month follows the current date, and the frontend budget page already behaved that way; keeping the backend default on the ledger tail made bootstrap and validation summaries disagree with the visible current-month budget view.
  Date/Author: 2026-06-12 / OpenCode

- Decision: replace the user-facing `Carried over` label with `Starting Available` and remove the top summary metric for that value.
  Rationale: the underlying formula is useful, but the old label was not clearly reconcilable to Aspire or to dojo's own category math.
  Date/Author: 2026-06-12 / OpenCode

## Outcomes & Retrospective

The aggregate audit is now implemented end to end. Import validation produces a first-class structured report instead of a coarse fixture snapshot, and the same report can be rerun through `python -m dojo.validation_cli` or the new `just validate-aggregates-*` recipes. Deterministic backend tests now cover report structure, hidden-entity summary semantics, and ignored budget-account net-worth diagnostics in addition to the earlier formula tests.

The audit also uncovered and fixed a real correctness bug: default visible budget summaries were counting hidden-category spending in `spent_minor`. The backend now respects `show_hidden` when computing spending totals, and the API/UI tests prove the visible and hidden-inclusive summaries diverge correctly.

The budget/accounts/net-worth UI surfaces are now more inspectable without adding a separate product-facing validation tool. Budget group panels show labeled columns and backend-provided group totals, account cards label their primary balance, the accounts page exposes the hidden-entity toggle directly, and the net-worth page labels the current total and distinguishes ignored imported budget valuations from native ledger totals.

The follow-up correction pass closed the three newly reported gaps as well. ATB now matches Aspire's `Dashboard!J3` / `Calculations!B59` semantics on both the deterministic fixture and the saved live-sheet dump. Net-worth rows are fully labeled, normalized duplicate budget-account snapshots are ignored in native totals, ambiguous normalized matches fail validation, and true tracking-only assets/debts still contribute to net worth. The old `Carried over` UI is gone; category and group tables now show `Starting Available`, and live-sheet spot checks confirmed cases like `Health Insurance` reconcile as `starting available = available` when current-month activity and budgeted movement are both zero.

Remaining risk: the real-sheet validation path is now fast enough to run against a saved dump, but live Google fetches still depend on local OAuth credentials. The API still emits FastAPI `on_event` deprecation warnings during tests, but they are unrelated to aggregate correctness.

## Context and Orientation

The current backend lives under `api/src/dojo/`. The import path starts in `api/src/dojo/importer.py`, persists data through `api/src/dojo/service.py`, and exposes aggregates through `api/src/dojo/api/routes.py`. The current validation pass is import-coupled and fixture-snapshot-based. The current frontend lives under `web/src/dojo/` and displays financial aggregates mainly on:

- `web/src/dojo/pages/BudgetPage.vue`
- `web/src/dojo/components/AvailableToBudgetCard.vue`
- `web/src/dojo/components/CategoryBudgetRow.vue`
- `web/src/dojo/components/AccountBalanceCard.vue`
- `web/src/dojo/components/PendingClearedBalanceBreakdown.vue`
- `web/src/dojo/pages/NetWorthPage.vue`

The deterministic import fixture is defined in `api/src/dojo/fixture_data.py`. Existing tests cover importer behavior, budget formulas, API endpoint smoke paths, and some Vue component rendering, but they do not yet prove exhaustive aggregate correctness against source-sheet semantics.

The source-of-truth boundaries for this audit are:

- Imported current ledger tables in DuckDB are dojo's native source of truth after import.
- Named ranges are the authoritative sheet interface for both import and validation.
- For account/category/month aggregates that Aspire computes from imported data, dojo should match Aspire exactly at the cent level unless a documented presentation-only rounding rule applies.
- For budget-account net worth, dojo should derive totals from imported budget account balances and treat duplicated Aspire valuation rows for those same budget accounts as expected diagnostic differences, not native totals.

## Plan of Work

First, extract aggregate validation into a dedicated backend layer that can build a structured report from a parsed workbook plus the imported DuckDB state. This layer should understand the consumed named ranges, compute Aspire-side expected aggregates from source ranges or known report cells/ranges, compute dojo-side actual aggregates from service/query methods, and emit comparable labeled checks with identifiers, month, source reference, expected cents, actual cents, delta cents, pass/fail state, and notes.

Next, route the current import-time validation through that layer and add a standalone developer command or script so validation can be rerun against an existing DuckDB import or a fetched real-sheet dump without changing application code. Keep the path deterministic for fixture tests, and document how to run the real-sheet path with OAuth or a saved dump.

Then deepen backend automated coverage. Add tests that prove core formulas independently from the higher-level validation report: account balances by status, standard-category activity and budgeted values, carryforward and availability, Available to Budget, credit-card payment-category behavior, hidden-entity exclusion and inclusion, month summary totals, and native net-worth derivation. Add API-level tests for any new validation surface and for aggregate values already returned by budget/accounts/net-worth endpoints.

Finally, audit the Vue aggregate displays against the backend contract. Add focused component/integration tests for labels, formatting, signs, and visible totals on budget, accounts, and net-worth surfaces. If the UI displays any aggregate that cannot yet be validated, remove it or label it clearly as unvalidated rather than leaving ambiguous numbers on screen. Update docs to explain the validation harness, aggregate source-of-truth rules, and any intentional Aspire-vs-dojo differences.

## Concrete Steps

Run all commands from the repository root inside the direnv-loaded Nix shell unless a subdirectory is explicitly stated.

1. Implement or update backend validation code, then run narrow backend tests:

       cd api && uv run pytest tests/test_importer.py tests/test_budget_formulas.py tests/test_api_endpoints.py

   Expected result: targeted importer/formula/API tests exit 0 and expose aggregate mismatches clearly on failure.

2. Add or update frontend aggregate display tests, then run focused web tests:

       cd web && pnpm test -- --run BudgetComponents App

   Expected result: aggregate display components render validated labels and amounts correctly.

3. Run the backend aggregate validation command against the deterministic fixture and, when credentials or a saved dump are available, against the real copied sheet.

   Expected result: the command writes or prints a structured report with labeled checks, source references, deltas, pass/fail, and explanatory notes.

4. Before completion, run the required repository workflows:

       just lint
       just typecheck
       just test
       just docs
       just container

   Expected result: commands exit 0, or any failure is documented with exact cause and recovery notes.

## Validation and Acceptance

This audit is accepted when:

- dojo exposes a backend validation path that can produce a structured aggregate report for fixture imports and a documented real-sheet path.
- The report covers at least account balances, credit-card balances, category availability, month activity, month budgeted, group totals where displayed, Available to Budget, month summary totals, hidden-account/category behavior, and net worth.
- Each check includes a stable label, source reference, expected Aspire-side value, actual dojo-side value, cent delta, pass/fail state, and explanatory notes.
- Deterministic tests prove the important aggregate formulas independently of the report machinery.
- API tests prove that budget/accounts/net-worth payloads expose the validated aggregate values used by the UI.
- UI tests prove that displayed aggregate labels, signs, and currency formatting match the validated backend values and do not accidentally include hidden entities unless toggled on.
- Any remaining dojo-vs-Aspire difference is explicitly documented with rationale, especially budget-account net-worth derivation and any unavoidable display-only rounding behavior.

## Idempotence and Recovery

Fixture validation must be repeatable against a fresh temporary DuckDB file. The validation command should be safe to rerun without mutating source sheets. Real-sheet validation may fetch live read-only data or read a previously dumped payload, but it must not modify the source workbook. If a validation run fails, the report should remain inspectable so the next run can focus on the failing aggregates. No destructive git or source-file rollback commands are needed.

## Interfaces and Dependencies

Expected interfaces after this work:

- Backend validation/report module under `api/src/dojo/`
- Standalone validation command or script callable from the repo
- Existing `DojoService` aggregate methods, possibly with extracted helpers for report generation
- Existing endpoints `GET /api/budget`, `GET /api/accounts`, and `GET /api/net-worth`
- Possibly a development-focused validation endpoint if it materially improves iteration without cluttering the product UI
- Updated tests in `api/tests/` and `web/tests/`

Relevant dependencies and artifacts:

- Deterministic fixture: `api/src/dojo/fixture_data.py`
- Live fetch/import helper: `api/src/dojo/live_sheet_harness.py`
- Source MVP contract: `mvp_spec.md`

## Artifacts and Notes

- The initial audit target is exhaustive aggregate correctness, not a domain-model expansion.
- Any discrepancy should be classified before fixing: importer parsing, formula semantics, Aspire interpretation, hidden/inactive handling, credit-card behavior, helper rows, net-worth derivation, API serialization, or UI display.
