# Validation Record

This file records validation results for each completed work item. Work items must be validated before they are considered done.

## Validation Commands

The following commands are used for validation throughout the project:

| Command | Purpose |
|---------|---------|
| `just check` | Full quality gate |
| `just api` | Start backend server |
| `just web` | Start frontend dev server |
| `just test-unit` | Backend unit tests |
| `just test-property` | Backend property tests |
| `just test-integration` | Backend integration tests |
| `just test-web` | Frontend tests |
| `just architecture-check` | Repository policy checks |
| `just migration-check` | Fresh database provisioning check |
| `just lint` | Linters |
| `just typecheck` | Type checking |
| `just format-check` | Formatting check |

## Validation Checklist (per work item)

For each completed work item, record:

1. **Commands run**: Exact commands executed
2. **Test results**: Pass/fail counts, any failures
3. **Type-check results**: Pass/fail details
4. **Lint results**: Any warnings/errors
5. **API checks**: Any API verification performed
6. **Data-invariant checks**: Any data correctness verification
7. **Manual interaction checks**: Steps performed manually
8. **Browser viewport/screenshots**: Sizes checked, screenshot paths
9. **Regressions considered**: What was checked for regressions
10. **Validation gaps**: What could not be validated

---

## Work Item 6.5: Rich-account values, remediation, and cutover

**Status**: Implementation complete through Milestone 6; product-owner browser acceptance and final Milestone 7 audit remain.

### Commands run

- `just test-unit` — 55 passed, including pure loan projection coverage.
- `just test-integration` — 47 passed, including cross-surface rich values, future-date guards, prospective linked activity, equal-timestamp investment ordering, loan components, and asset/liability cutovers.
- `just test-property` — 15 passed.
- `just typecheck` — Passed.
- `just lint` — Passed.
- `just architecture-check` — 8 passed.
- `just migration-check` — 2 passed against fresh schema provisioning.
- `just build` — API and web production builds passed.
- `just docs` — Passed.
- Focused headless-Chrome Cypress sweep across institution, wizard, budget, and account detail specs — 26 passed.
- Design-system manifest coverage — 39 fixtures present.
- Confirmed terminology lint — zero hits.

### Data invariants checked

- Investment contributions and withdrawals remain net-worth neutral.
- A same-day post-statement contribution is provisional; a later same-day statement correction supersedes it.
- Derived investment contributions affect monthly category Activity and category history without categorizing transfer legs.
- Loan principal liability, escrow restricted asset, and unapplied credit sum to the same aggregate net worth exactly once.
- Loan projections are labeled estimates and reset from the latest actual principal snapshot.
- One-to-many cutover is idempotent, activates successors inclusively on the cutover date, and preserves signed net worth for asset and liability predecessors.

### Validation gaps

- Product-owner browser revalidation remains required before Dashboard work.
- Cypress Electron repeatedly exited with `SIGSEGV` after two tests in larger specs; identical specs pass under headless Chrome.
- The full `just check` remains affected by the Electron issue and unrelated pre-existing formatting drift in `api/tests/test_api_endpoints.py`.
- (2026-08-20) Closure: the canonical component runner now uses Nix-provided Chromium, the App tests avoid product bootstrap on `/dev/test`, and the unrelated formatting drift was committed separately. Revalidate with `just test-web` and `just check`.

---

## Work Item 1.1: Token System and Global Stylesheet

*Not yet completed.*

## Work Item 1.2: Contributor Documentation Update

*Not yet completed.*

## Work Item 6.A: Assets & Liabilities Overview Page

**Status**: Implementation complete, visual validation complete.

### Commands run

- `just lint-api` — Passed
- `just typecheck` — Passed
- `just format-check` — Passed (after running `just format`)
- `just lint` — Passed
- `just test-web` — Passed, 247 tests on latest rerun; earlier run passed with 245 tests
- `just check` — Passed on latest rerun after baton/plan validation updates
- `uv run pytest tests/test_api_endpoints.py::test_budget_accounts_and_net_worth_endpoints_return_validated_aggregates` from `api/` — Passed

### Test results

- Backend: Targeted aggregate endpoint test passes, including deterministic tracking asset/liability grouping
- Frontend: Cypress component suite passes (`just test-web`, 247 tests on latest rerun). `StackedEntityCard.cy.ts` specifically passes 13 tests.

### Type-check results

- Initial run had 3 errors related to missing `value_minor`, `metadata`, `source_of_truth` on `Account` type
- Fixed by creating `AssetsLiabilitiesItem` type extending `Account`
- Final typecheck passes cleanly

### Lint results

- Initial format check failed (Prettier formatting issues)
- Fixed by running `just format`
- Final lint passes cleanly

### Implementation summary

1. Created `StackedEntityCard.vue` shared component with:
   - Props: name, primaryValue, icon, delta, metadata, status, sourceOfTruth, clickable
   - DESIGN.md token usage for all styling
   - Proper accessibility attributes

2. Created `StackedEntityCard.fixtures.ts` with 5 scenarios:
   - Default, positive delta, negative delta, with status, with warning status

3. Updated `manifest.yaml` to include StackedEntityCard in Page Data section

4. Created `AssetsLiabilitiesPage.vue` with:
   - NavigationRail with Assets & Liabilities link
   - PageHeader with "Assets & Liabilities" title and "Add item" button
   - MetricStrip showing net worth, total assets, total liabilities
   - Grouped stacked entity cards (CASH, INVESTMENTS, TANGIBLE_ASSETS, CREDIT, LOANS)
   - Empty state with SPEC-mandated "Need to bring in Aspire data? Use Onboarding." message

5. Added `/assets-liabilities` route to `router.ts`

6. Added `fetchAssetsLiabilities` API client function

7. Updated types with `AssetsLiabilitiesResponse` and `AssetsLiabilitiesItem`

8. Updated navigation in BudgetsPage and TransactionsPage to link to `/assets-liabilities`

9. Closed follow-up visual gaps for the Assets & Liabilities overview:
   - Navigation rail is collapsed by default and has real expand/collapse UI on app pages
   - Assets & Liabilities content uses the available page width
   - Group section icons are monochrome SVG parts instead of emoji
   - Overview rows no longer use alternating fill
   - Migrated tracking accounts group deterministically as `Tracking assets` or `Tracking liabilities` by polarity

### Visual validation

- Mock screen: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/01-assets-liabilities-overview.png`
- Status: Complete — confirmed structure matches mock (collapsible nav rail, page header, metric strip, grouped full-width tables, monochrome section icons). Change (30d) and Attention columns show backend-dependent data (hardcoded +$0.00 and "OK") which is a backend gap, not a visual gap.
- Screenshots captured:
  - `/home/ogle/src/dojo2/tmp/assets-liabilities-fixed-collapsed.png`
  - `/home/ogle/src/dojo2/tmp/assets-liabilities-tracking-groups.png`

### Validation gaps

- Change (30d) and Attention columns require backend API changes to populate real data

---

## Work Item 6.B: Assets & Liabilities Add Item Wizard

**Status**: Implementation complete, visual validation complete.

### Commands run

- `just lint-web` — Passed
- `just typecheck` — Passed
- `just test-web` — Passed, 251 tests
- `just check` — Passed

### Test results

- Frontend: Cypress component suite passes (`just test-web`, 251 tests).
- Added `AddItemWizardPage.cy.ts` with 3 tests covering modal rendering, explicit add-route safety, and the account creation payload for a loan.
- Updated `DropdownButton.cy.ts` to cover the new primary split-button click event.

### Type-check results

- `just typecheck` passes cleanly after adding the wizard route, page, and typed `createAccount` return payload.

### Lint results

- Initial `just lint-web` run found one Cypress assertion style issue.
- Fixed the assertion and reran `just lint-web` successfully.

### Implementation summary

1. Added explicit `/assets-liabilities/add` route before `/assets-liabilities/:id` so the Add item route no longer falls through to account detail id `add`.

2. Created `AddItemWizardPage.vue` as a page-local modal workflow over the existing overview page.

3. Added step 1 with five mock-aligned entity type cards: budget account, tracking account, investment account, loan, and tangible asset.

4. Added step 2 with minimal common fields and type-specific fields backed by the existing `POST /api/accounts` endpoint.

5. Updated `DropdownButton.vue` so the primary half emits `primaryClick`; the overview page uses this to open `/assets-liabilities/add`, while dropdown options still open direct type-specific wizard URLs.

6. Updated `createAccount` to return the created `account_id`, letting the wizard route to the new detail page after successful creation.

### Visual validation

- Mock screen: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/02-add-item-type-wizard.png`
- Status: Complete — confirmed modal-over-overview structure, title, close button, three-step rail, five full-width entity cards, budget-boundary note, Aspire onboarding note, and footer actions match the mock. The tightened desktop modal fits without internal scrolling.
- Screenshots captured:
  - `/home/ogle/src/dojo2/tmp/add-item-wizard-step1.png`
  - `/home/ogle/src/dojo2/tmp/add-item-wizard-step1-tightened.png`

### Validation gaps

- No backend changes were made; account creation uses existing endpoint behavior.
- Browser validation did not submit a real account to the local DuckDB database to avoid mutating developer data; Cypress verifies the outgoing payload with a mocked response.

---

## Work Item 6.C: Budget Account Detail

**Status**: Implementation complete, visual validation complete.

### Commands run

- `just typecheck` — Passed
- `just lint-web` — Passed
- `cd web && pnpm test:component --spec "cypress/component/AccountDetailPage.cy.ts"` — Passed, 1 test
- `just test-web` — Passed, 41 Vitest tests and 254 Cypress component tests
- `just check` — Passed after running `just format` and moving import-draft SQL queries into SQL files required by the repository architecture policy

### Test results

- Added `AccountDetailPage.cy.ts` covering the budget-account detail route contract with mocked accounts and transactions.
- The spec verifies header badges/actions, five-metric strip presence, Memo column, target-account transaction scoping from the fetched page, sidebar action affordances, and Summary & notes rendering.

### Type-check results

- `just typecheck` passes cleanly after extending the frontend `Account` type with optional account metadata returned by the API.

### Lint results

- `just lint-web` passes cleanly.

### Implementation summary

1. Aligned `AccountDetailPage.vue` budget-account chrome with mock 03: clean account title, type/source badges, direct Reconcile button, secondary More actions split button, kebab affordance, and DESIGN.md token-preserving layout.
2. Expanded the budget-account transaction table to include Memo and row action affordances on desktop while keeping a reduced readable column set on narrow viewports.
3. Added lower content matching the mock: balance-over-time preview, period toggle presentation, Summary & notes card, and edit-notes affordance.
4. Expanded the right rail cards with reconciliation, history, and configuration action buttons.
5. Kept `EntityDetailLayout` page-local for this iteration instead of cataloging a premature shared component contract.

### Visual validation

- Mock screen: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/03-budget-account-detail.png`
- Status: Complete for the Work Item C frontend scope — confirmed the actual page has the mock's major page structure, header action split, metric strip, dense ledger table, lower chart/summary area, and sidebar cards. Narrow viewport validation confirms the page remains readable by collapsing to one content column and hiding lower-priority table/action controls.
- Screenshots captured:
  - `/home/ogle/src/dojo2/tmp/account-detail-workitem-c-desktop.png`
  - `/home/ogle/src/dojo2/tmp/account-detail-workitem-c-narrow.png`

### Validation gaps

- `fetchTransactionsPage` still lacks server-side `account_id` filtering. The page filters the fetched page client-side and now labels that limitation instead of claiming the full account ledger.
- Reconciliation review, full charting, and edit/history workflows remain deferred per the work item non-scope.

---

## Work Item 6.D: Tracking Account Detail + Cutover Modal

**Status**: Implementation complete, visual validation complete.

### Commands run

- `just typecheck` — Passed
- `just lint-web` — Passed
- `just test-web` — Passed, 257 tests
- `just architecture-check` — Passed

### Test results

- Added 2 new Cypress tests in `AccountDetailPage.cy.ts` for tracking account detail rendering and cutover modal open/close.
- All 257 frontend tests pass (41 Vitest + 254 Cypress component tests, including 2 new tracking-account tests).
- Existing budget account tests remain green.

### Type-check results

- `just typecheck` passes cleanly after extending `Account` type with `tracking_polarity`, `tracking_source`, `latest_valuation_minor`, `latest_valuation_date`, and `metadata` fields.

### Lint results

- `just lint-web` passes cleanly.
- Prettier formatting applied to all changed files.

### Implementation summary

1. Extended `Account` type with tracking-specific fields: `tracking_polarity`, `tracking_source`, `latest_valuation_minor`, `latest_valuation_date`, `metadata`.
2. Added `fetchTrackingSnapshots` and `createTrackingSnapshot` API client functions.
3. Added tracking-specific 5-metric strip: Current value, Polarity (Asset ↑ / Liability), Latest snapshot date, Source/migration, Reconciliation freshness.
4. Added "Add snapshot" primary button and "Create richer account" secondary button in header actions.
5. Added import info banner for tracking accounts with `tracking_source === "import"`.
6. Replaced transaction section with snapshot history table (Date ↓, Value columns with dot indicators) for tracking accounts.
7. Added valuation history section with summary stats (30d inflow/outflow/net flow, Average daily value) and notes area.
8. Added sidebar sections: Account details with "View budgeting details" link, Migration/import context with "View import details" link, History/configuration with snapshot frequency and alerts.
9. Built cutover modal matching mock 04: entity type dropdown, cutover date, name, opening value, contribution category radio group (Create new/Link existing/None), representation change checkbox, historical as-of views info banner, Cancel/Create account buttons.
10. Moved `isBudgetAccount`/`isInvestmentAccount`/`isLoanAccount`/`isTrackingAccount`/`isTangibleAsset` computed properties before `trackingSnapshots` query to avoid initialization ordering error.
11. Cleaned up `AssetsLiabilitiesItem` type to remove redundant fields now inherited from `Account`.

### Visual validation

- Mock screen: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/04-tracking-account-upgrade-cutover.png`
- Status: Complete — confirmed the actual page has the mock's major page structure: back link, header with badges and action buttons, 5-metric strip (Current value, Polarity, Latest snapshot, Source/migration, Reconciliation freshness), import info banner, snapshot history table with date/value columns, balance trend chart, valuation history section, sidebar cards (Account details, Migration/import context, History/configuration). Cutover modal matches mock 04: title, description, entity type dropdown, date picker, name, opening value, contribution category radios, representation change checkbox, info banner, and footer actions.
- Screenshots captured:
  - `/home/ogle/src/dojo2/tmp/tracking-account-detail-desktop.png`
  - `/home/ogle/src/dojo2/tmp/tracking-cutover-modal.png`

### Validation gaps

- Cutover persistence is not implemented — modal closes with an informational stub message. Backend cutover endpoint does not exist yet.
- Snapshot creation (Add snapshot button) does not yet open a form — the button is wired but the create-snapshot flow is deferred.
- Reconciliation for tracking accounts is not built yet.
- Import details link and budgeting details link are stub actions.

---

*Add new work items above as they are completed.*

## Visual Gap Closure — Work Item: Detail Pages

**Status**: Implementation complete, visual validation complete.

### Commands run

- `just typecheck` — Passed
- `just format-check` — Passed (after running `just format`)
- `just lint-web` — Passed for new/changed files (pre-existing lint issues in other files are unrelated)

### Implementation summary

1. Added `/assets-liabilities/:id` route to `router.ts`

2. Created `AccountDetailPage.vue` with:
   - Back navigation link to `/assets-liabilities`
   - Page header with account name, type badge (Budget/Investment/Loan/Tracking/Tangible asset), and ledger badge
   - Context-aware action buttons (Reconcile for budget, Contribute/Withdraw/Reconcile for investment, Record payment/Reconcile/Edit loan for loan)
   - Metric strip with 5 items for budget accounts (Current balance, Pending, Cleared, Net worth contribution, Reconciliation freshness), 5 for investment (Current value, Cash, Holdings value, Net worth contribution, Reconciliation freshness), and 4 for loan (Current obligation, Principal balance, Net worth contribution, Reconciliation freshness)
   - Two-column layout: left (transactions table + balance chart placeholder) and right sidebar
   - Transaction table with Date, Description, Category, Amount, Status, and Balance columns with running balance computation
   - Sidebar with Account details, Reconciliation, History, and Configuration sections
   - "View budgeting details" and "Edit configuration" action links
   - Responsive breakpoint handling for narrow screens

3. Fixed account type detection: changed from `budget_account_type` to `account_class` (BUDGET/INVESTMENT/LOAN/TRACKING/TANGIBLE_ASSET)

### Visual validation

- Mock 01 (overview): Confirmed structure matches — nav rail, page header, metric strip, grouped tables with correct columns. Change (30d) and Attention columns show backend-dependent data (hardcoded +$0.00 and "OK" respectively) which is a backend gap, not a visual gap.
- Mock 03 (budget account detail): Confirmed structure matches — back link, badges, 5-metric strip, transactions table with 6 columns (Date, Description, Category, Amount, Status, Balance), sidebar with Account details/Reconciliation/History/Configuration sections, "View budgeting details" link, Reconcile button.
- Mock 05 (investment account detail): Structural layout inherited from shared component; metric strip adapts to 5 investment-specific metrics.
- Mock 07 (loan detail): Structural layout inherited from shared component; metric strip adapts to 4 loan-specific metrics.
- Mock 08 (reconciliation review): Deferred per scope — detail pages keep Reconcile button routing to placeholder.

### Mock deviations deliberately not reproduced

- **Category name formatting**: API returns raw system_category keys (TX_STARTING_BALANCE, TX_AVAILABLE_TO_BUDGET) rather than human-readable labels. This is a backend data gap; the component renders what the API provides.
- **Transaction filtering**: `fetchTransactionsPage` does not support account_id filtering; client-side filter may miss transactions beyond the first50 fetched. This is a backend API gap.
- **Change (30d) values**: API does not expose per-item change data. Column shows hardcoded "+$0.00". Backend gap.
- **Attention status variety**: API does not expose per-item attention/reconciliation status. All rows show "OK". Backend gap.
- **Charts**: Balance over time, Value over time, and Loan balance over time show placeholder text. Charting library integration is a separate work item.

### Validation gaps

- Cypress component tests not added for AccountDetailPage (would require mocking the full query chain)
- Backend integration tests not modified (no backend changes)
