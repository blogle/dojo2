# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 6.5 — Assets & Liabilities Completion

Current work-item status: **In progress — final mock-alignment and inert-control audit**

## Product and repository context

The dojo application is a local-first personal finance tool with a FastAPI + DuckDB backend and Vue 3 frontend. The existing application has working onboarding (fixture/Google Sheet import), budget view, transaction listing/CRUD, account management, category management, and net-worth reporting. The frontend uses a NavigationRail sidebar and DESIGN.md-compliant tokens.

`SPEC.md` defines the canonical product behavior. `DESIGN.md` defines the canonical visual and interaction design system. Both must be used as the sources of truth going forward.

Canonical requirements:
- `SPEC.md` — product behavior
- `DESIGN.md` — visual design, tokens, components

Relevant contributor guidance:
- `CONTRIBUTING.md` — workflow and commands
- `AGENTS.md` — agent routing
- `ARCHITECTURE.md` — runtime structure

## Completed work

- (2026-07-07) Created ExecPlan for Assets & Liabilities frontend flows.
- (2026-07-07) Work Item A (Overview Page) — Complete:
  - Created `StackedEntityCard.vue` shared component with fixtures and manifest entry.
  - Created `AssetsLiabilitiesPage.vue` with PageHeader, MetricStrip, grouped stacked entity cards.
  - Added `/assets-liabilities` route to router.
  - Added `fetchAssetsLiabilities` API client function.
  - Updated types with `AssetsLiabilitiesResponse` and `AssetsLiabilitiesItem`.
  - Updated navigation in BudgetsPage and TransactionsPage to link to `/assets-liabilities`.
  - Ran visual validation against `01-assets-liabilities-overview.png` and recorded results in `VALIDATION.md`.
  - Confirmed `StackedEntityCard.cy.ts` passes as part of `just test-web`.
  - Relevant commits: `c320091 feat(assets-liabilities): add overview page with StackedEntityCard component`, `6dd7165 fix(assets-liabilities): align visual appearance with mock 01`.
- (2026-07-07) Detail-page visual gap closure — Complete for current committed scope:
  - Added `/assets-liabilities/:id` route and `AccountDetailPage.vue`.
  - Added budget, investment, and loan detail layouts with contextual metrics/actions.
  - Recorded visual validation in `VALIDATION.md`.
  - Relevant commit: `1f5ee4e feat(assets-liabilities): add detail view and polish navigation`.
- (2026-07-07) Work Item B (Add Item Wizard) — Complete:
  - Added explicit `/assets-liabilities/add` route before `/assets-liabilities/:id`.
  - Created `AddItemWizardPage.vue` as a modal workflow over the overview page.
  - Added five entity-type choices, type-specific details fields, and submit wiring to `POST /api/accounts`.
  - Updated `DropdownButton.vue` so the primary Add item button opens the wizard while dropdown choices remain type-specific shortcuts.
  - Added Cypress coverage for wizard rendering, route safety, account creation payloads, and primary split-button clicks.
  - Ran visual validation against mock `02-add-item-type-wizard.png` and recorded results in `VALIDATION.md`.
  - Relevant commit: `c572696 feat(assets-liabilities): add item wizard`.
- (2026-07-08) Onboarding import review and Assets & Liabilities wizard remediation — Complete:
  - Added Aspire import analyze/review/commit flow with editable net-worth category decisions and low-confidence confirmation.
  - Added backend `import_drafts` persistence plus `/api/import/google-sheet/analyze` and `/api/import/google-sheet/commit` endpoints.
  - Changed Assets & Liabilities `Add item` from a dropdown to a plain primary button.
  - Removed stale onboarding copy and removed low-value fields from tracking, investment, and tangible asset creation forms.
  - Added investment-account `self_managed` and `tax_treatment` metadata through API models, SQL schema, frontend form payloads, and Cypress coverage.
  - Fixed import details modal rendering for review-based imports that have `import_summary` and `decisions_summary` but no legacy `validation_report`.
  - Protected `/budgets` route loading by lazy-loading `vue-draggable-plus` only when category reordering is enabled, while pre-optimizing it for Vite/Cypress stability.
  - Relevant commit: `d27913b feat(onboarding): add import review flow`.
- (2026-07-09) Work Item C (Budget Account Detail) — Complete:
  - Aligned `/assets-liabilities/:id` budget-account detail rendering to mock 03 with split header actions, five-metric strip, dense ledger table including Memo/action affordances, balance chart preview, Summary & notes panel, and full sidebar action cards.
  - Added focused Cypress coverage in `web/cypress/component/AccountDetailPage.cy.ts`.
  - Decided not to extract or catalog `EntityDetailLayout` yet because the current page shell remains account-class-specific and is not a durable shared catalog contract.
  - Moved import-draft SQL statements into `api/src/dojo/sql/queries/*.sql` to satisfy the repository architecture policy surfaced by `just check`.
  - Relevant commit subject: `feat(assets-liabilities): align budget account detail`.
- (2026-07-09) Scoped transaction ledger and account detail refinements — Complete:
  - Added server-side transaction filtering (`account_id`, `category_id`, `status`, `date_from`/`date_to`, `amount_min`/`max`) via parameterized DuckDB queries replacing ad-hoc hidden-account/category SQL variants with a unified filter-clause builder.
  - Added `status_counts` to the transaction page response, computed over the full filtered set (not the page).
  - Added `TransactionFilterBar` prop-lift: filter state is now owned by the page, enabling locked-account mode and infinite-scroll filter re-queries.
  - Replaced client-side transaction table in `AccountDetailPage.vue` with `TransactionLedger` + `TransactionFilterBar`, infinite-scroll via `useInfiniteQuery`, locked account filter, running-balance column, load-more trigger, edit/delete mutations.
  - Added `BalanceTrendChart.vue` with period selector, SVG line chart, hover, drag-measurement, and tooltip.
  - Added edit-configuration `FormModal` for account metadata with retire-account action.
  - Added Cypress coverage for edit-configuration submit, balance-trend-chart visibility, and removed assertions for deleted history/configuration sidebar sections.
  - Relevant commit: `30d8ac3 feat(transactions): add scoped account ledger`.
- (2026-07-09) Server-side summary and chart computation in DuckDB — Complete:
  - Created `account_transaction_summary.sql` — windowed aggregate (inflow/outflow/net/count) + daily-spine average daily balance via `generate_series` + cumulative sum anchored to `display_balance_minor`.
  - Created `account_balance_series.sql` — per-transaction-day balance via backward window cumulative from anchor, downsampled per period bucket (`date_trunc` to day/week/month).
  - Added `GET /api/accounts/{id}/transactions/summary` and `GET /api/accounts/{id}/balance-trend` routes.
  - Added service methods `account_transaction_summary`, `account_balance_trend`, and `_account_display_balance` helper.
  - Updated `AccountDetailPage.vue` to fetch summary and trend as independent `useQuery` calls keyed by account/period, removing client-side paged-derived computations.
  - Chart now refetches when period selector changes; summary is fixed 30-day window independent of ledger filter.
  - Added integration tests validating both endpoints against reference Python computation using the same anchored-daily-spine formula.
  - Relevant commit: `5ba2d8f fix(account-detail): compute summary and chart server-side in DuckDB`.
- (2026-07-09) Work Item D (Tracking Account Detail + Cutover Modal) — Complete:
  - Extended `Account` type with tracking-specific fields (`tracking_polarity`, `tracking_source`, `latest_valuation_minor`, `latest_valuation_date`, `metadata`).
  - Added `fetchTrackingSnapshots` and `createTrackingSnapshot` API client functions.
  - Aligned tracking account detail page with mock 04: 5-metric strip (Current value, Polarity, Latest snapshot, Source/migration, Reconciliation freshness), import info banner, snapshot history table, balance trend chart, valuation history section with summary stats and notes.
  - Added header actions: "Add snapshot" primary button, "Create richer account" secondary button.
  - Added sidebar sections: Account details with "View budgeting details" link, Migration/import context with "View import details" link, History/configuration with snapshot frequency and alerts.
  - Built cutover modal matching mock 04: entity type dropdown, cutover date, name, opening value, contribution category radio group, representation change checkbox, historical as-of views info banner, Cancel/Create account buttons.
  - Added Cypress coverage for tracking account detail rendering and cutover modal open/close (2 new tests, 257 total).
  - Ran visual validation against mock 04 and recorded results in `VALIDATION.md`.
  - Relevant commit: `feat(assets-liabilities): align tracking account detail with mock 04`.
- (2026-08-01) Rich-account value and remediation milestones 1–6 — Implemented:
  - Committed the initial tracking/tangible/investment/loan checkpoint as `f959bcf`.
  - Blocked future financial snapshots/statements while preserving future cutover scheduling.
  - Added a shared institution free-text combobox with curated and prior-account suggestions.
  - Moved investment contribution and loan payment categories into account creation/configuration.
  - Fixed same-day provisional investment ordering and derived contribution Activity/history.
  - Added cash-only investment statements.
  - Added required loan current principal/as-of, optional lender YTD checkpoints, pure estimated amortization, and separately presented escrow/unapplied-credit assets.
  - Added atomic idempotent one-to-many tracking cutover with inclusive effective activation.

## Current repository state

- **Branch**: `master`
- **Working tree**: Rich-account remediation and deterministic browser acceptance are committed; local untracked `tmp/` contains visual-review artifacts and must not be committed.
- **Last completed implementation task**: Seven-scenario deterministic browser acceptance with measured performance budgets.
- **Known failing checks**: None. `just check` and `just test-e2e` pass with Nix-provided Chromium.
- **Required services**: DuckDB (provisioned by `just api`), Google OAuth (optional)
- **Feature flags**: None
- **Aspire data**: Deterministic fixture available at `fixture://default`

## Capability and dependency status

Backend capabilities already exist:
- `GET /api/assets-liabilities` returns grouped cards with source_of_truth, value_minor, group_totals, asset/liability/net totals.
- `POST/PUT /api/accounts`, `GET /api/accounts`.
- Snapshot/valuation CRUD: positions, cash-snapshots, price-snapshots, tracking-snapshots, loan-snapshots, tangible-valuations.
- `GET /api/transactions` with server-side filtering: `account_id`, `category_id`, `status`, `date_from`/`date_to`, `amount_min_minor`/`amount_max_minor`, plus `status_counts` in response.
- `GET /api/accounts/{id}/transactions/summary` — windowed aggregate (inflow, outflow, net flow, count, average daily balance) pushed to DuckDB.
- `GET /api/accounts/{id}/balance-trend` — anchored balance timeseries downsampled per period bucket, pushed to DuckDB.
- Type-aware current/as-of values for tracking, tangible, investment, and loan accounts.
- Investment statement reconciliation, configured contribution links, provisional transfer deltas, and derived category activity/history.
- Loan opening snapshots, configured payment attribution, statement reconciliation, YTD checkpoints, and estimated amortization.
- Atomic `POST /api/accounts/{tracking_id}/cutovers` one-to-many representation change.

Frontend capabilities now present:
- Overview page with `/assets-liabilities` route
- StackedEntityCard shared component
- Account detail page at `/assets-liabilities/:id` with budget, investment, loan, tracking, and tangible-asset type handling
- Budget-account detail page now exposes mock-03-aligned header actions, metrics, scoped transaction table, chart/summary area, reconciliation/history/configuration affordances, and responsive narrow rendering.
- Tracking-account detail page exposes snapshot source/date/freshness without a premature reconciliation state.
- Cutover modal supports multiple investment, loan, and tangible successors, opening components, institutions, category links, combined-value variance, and persisted representation change.
- Investment detail supports cash-only/holdings statements, contribution/withdrawal behavior, category balance preview, and same-day provisional value.
- Loan detail separates lender actual, balance-derived, estimated, unknown, liability, and restricted-asset information.
- Transaction filter bar with account/date/category/amount/status filters; account filter can be locked to the current account on the detail page.
- `TransactionLedger` virtualized table with running-balance column, infinite-scroll load-more, edit/delete mutations, and locked-account support.
- `BalanceTrendChart` SVG component with period selector, hover crosshair, drag-measurement tooltip, and server-side-downsampled data.
- Edit-configuration `FormModal` for account metadata with retire-account action.
- Summary and balance trend fetched as independent server-side queries, no longer derived from the paged transaction ledger.
- Add item wizard at `/assets-liabilities/add` with type selection and minimal account creation forms. The overview header now uses a plain `Add item` button; direct type shortcuts are no longer exposed from the overview header.
- Onboarding import review flow that analyzes Aspire data, lets users review every net-worth category treatment, asks for simple low-confidence confirmation, then commits the reviewed import.
- Import details modal supports both legacy validation-report imports and review-based imports with imported-record counts and net-worth decision summaries.
- Budget page route loading is resilient to `vue-draggable-plus` optimized dependency load issues because draggable behavior is loaded only when reorder mode is enabled.

Frontend capabilities still planned:
- Final mock-alignment/inert-control audit before Dashboard work.

## Next work item

**Phase 6.5: final Assets & Liabilities acceptance**

Dashboard work is blocked until Assets & Liabilities is financially correct and its proposed flows are complete. The authoritative living plan is `docs/plans/complete-assets-liabilities.md`.

Milestones 1–6 and deterministic browser acceptance are implemented. The remaining work is the final mock/inert-control review.

### Definition of done

1. Type-specific values agree across account detail, Assets & Liabilities, and net worth for any effective date.
2. Every visible action in mocks 01–07 either works or is removed; no fabricated financial state remains.
3. Tracking, tangible, investment, loan, and one-to-many cutover acceptance scenarios pass. Complete.
4. `just check` passes and visual validation is recorded in `VALIDATION.md`. Quality gate complete; subjective final visual audit remains.

## Human decisions required

None for the planned scope. Product decisions made on 2026-07-31 are recorded in `SPEC.md`, `DECISIONS.md`, and `docs/plans/complete-assets-liabilities.md`.

## Known risks and observations

- The `StackedEntityCard` component uses simplified metadata display. May need enhancement for more complex entity types.
- The overview page currently shows all groups. May need filtering or sorting options in future.
- The latest onboarding import review work intentionally counts unique Aspire net-worth categories for decision summaries, not raw valuation rows.
- `vue-draggable-plus` is now a lazy dependency of `HierarchicalCategoryTable.vue`; tests that mount reorder mode may need Vite optimized-dependency prewarming, which is handled by `web/vite.config.ts`.
- The balance trend chart's `BalanceTrendPoint` type (`date` + `valueMinor`) differs from the API response type (`date` + `balance_minor`); the mapping is explicit in `AccountDetailPage.vue`. Both should be kept aligned if the chart component is reused elsewhere.
- The `_account_display_balance` helper loads all accounts to find one; acceptable for the small account set, but could be replaced with a direct query if performance becomes a concern.
- The canonical Cypress recipe uses Electron, which is unstable for the larger account specs in the current environment; headless Chrome is the successful fallback evidence.

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
