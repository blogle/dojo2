# ExecPlan: Assets & Liabilities Frontend Flows

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

After this work, dojo will have a complete Assets & Liabilities frontend surface: an overview page showing all financial entities grouped by type, detail pages for each entity class (budget accounts, tracking accounts, investment accounts, loans, tangible assets), and flows for adding new entities, making contributions, payments, and managing valuations. Users will be able to see their complete net worth breakdown, drill into individual accounts, and perform account-specific operations.

## Progress

- [x] (2026-07-07) Created ExecPlan for frontend implementation.
- [x] (2026-07-07) Work Item A: Overview page with `/assets-liabilities` route, MetricStrip, grouped stacked entity cards, Cypress component coverage, and visual validation against mock 01.
- [x] (2026-07-07) Work Item B: Add item wizard with explicit `/assets-liabilities/add` route, entity type selection, type-specific account forms, and Cypress coverage.
- [x] (2026-07-09) Work Item C: Budget account detail page aligned to mock 03 with split header actions, dense metric strip, scoped transaction table with memo/action affordances, balance chart preview, summary/notes panel, full sidebar action cards, focused Cypress coverage, and visual validation. `EntityDetailLayout` was not extracted or cataloged because the current shell still contains account-class-specific decisions and would not yet be a reusable fixtureable catalog contract.
- [ ] Work Item D: Tracking account detail page + cutover modal.
- [ ] Work Item E: Investment account detail page + contribution flow.
- [ ] Work Item F: Loan detail page + payment flow.
- [ ] Work Item G: Tangible asset detail page.
- [ ] Work Item H: Settlement state presentation (StateBadge extensions).

## Surprises & Discoveries

- Observation: The committed overview dropdown currently pushes `/assets-liabilities/add?type=...`, but the router only defines `/assets-liabilities` and `/assets-liabilities/:id`. Until Work Item B adds an explicit `/assets-liabilities/add` route before the dynamic `:id` route, selecting Add item can be interpreted as an account detail route for id `add`.
  Evidence: `web/src/dojo/router.ts` defines `/assets-liabilities/:id`; `web/src/dojo/pages/AssetsLiabilitiesPage.vue` pushes `/assets-liabilities/add?type=${key}`.

- Observation: Browser validation found the first add-wizard modal initially used too much vertical space and created an inner scrollbar on a desktop viewport.
  Evidence: The first screenshot at `/home/ogle/src/dojo2/tmp/add-item-wizard-step1.png` showed the boundary note partly below the modal body scroll. Tightening card height and modal spacing produced `/home/ogle/src/dojo2/tmp/add-item-wizard-step1-tightened.png`, which fits the full first step like mock 02.

- Observation: The existing transaction API does not support account-id filtering, so the detail page can only filter the currently fetched transaction page in the browser. This makes full transaction counts and pending/cleared counts incomplete for accounts whose activity is outside the first fetched page.
  Evidence: Browser validation of `/assets-liabilities/ed588f91-4e40-5da5-bcc2-086de7f8cb59` showed 10 scoped rows from a transaction page whose unscoped total was 10523. The page now labels this as scoped current-page data instead of claiming a full account ledger.

## Decision Log

- Decision: Create ExecPlan for frontend implementation separate from domain model ExecPlan.
  Rationale: The domain model ExecPlan covers backend schema and service work. This plan covers frontend page composition and UI flows.
  Date/Author: 2026-07-07 / opencode

- Decision: Start with Work Item A (overview page) as it establishes the route and page structure.
  Rationale: The overview page is the entry point for all Assets & Liabilities functionality and establishes the API integration pattern.
  Date/Author: 2026-07-07 / opencode

- Decision: Keep the Add item wizard page-local rather than adding it to the design-system catalog.
  Rationale: The wizard is a SPEC-specific workflow assembled from existing design-system primitives and does not yet define a reusable component contract.
  Date/Author: 2026-07-07 / opencode

- Decision: Add `/assets-liabilities/add` before `/assets-liabilities/:id` and let the overview split button open that route from its primary half.
  Rationale: Route order prevents `add` from being interpreted as an account id, and the primary Add item action now matches mock 02 while dropdown selections remain direct type shortcuts.
  Date/Author: 2026-07-07 / opencode

- Decision: Do not extract or catalog `EntityDetailLayout` during Work Item C.
  Rationale: The current `AccountDetailPage.vue` chrome is reused internally across budget, investment, loan, tracking, and tangible account branches, but its slots and sidebar content are still shaped by account-class-specific decisions. Cataloging it now would create a premature design-system contract. The budget-account detail alignment can be completed with smaller page-local edits and focused route coverage.
  Date/Author: 2026-07-09 / opencode

## Outcomes & Retrospective

### Work Item A Progress (2026-07-07)

**What was achieved:**
- Created `StackedEntityCard.vue` as a new shared component with proper DESIGN.md token usage, fixtures, and manifest entry.
- Created `AssetsLiabilitiesPage.vue` with PageHeader, MetricStrip, and grouped stacked entity cards.
- Added `/assets-liabilities` route to the Vue router.
- Added `fetchAssetsLiabilities` API client function and corresponding TypeScript types.
- Updated navigation in BudgetsPage and TransactionsPage to link to the new route.
- All lint, typecheck, and format checks pass.

**What remains:**
- Work Item B must add the `/assets-liabilities/add` route and wizard so the existing Add item dropdown no longer falls through to the dynamic detail route.

**Lessons learned:**
- The existing Account type needed extension with `value_minor`, `source_of_truth`, and `metadata` fields for the assets-liabilities response.
- The navigation pattern is page-level (each page includes NavigationRail), not global layout.
- DESIGN.md tokens are already available as CSS custom properties, making component styling straightforward.

### Work Item A Completion (2026-07-07)

Work Item A is complete. The overview page, route, API client integration, shared `StackedEntityCard` component, component fixtures, manifest entry, Cypress component tests, validation record, visual validation artifacts, and commit history are present. The latest rerun of `just test-web` passes 247 Cypress component tests, including 13 `StackedEntityCard` tests. The latest rerun of `just check` passes after the plan and baton refresh.

### Detail Page Visual Gap Closure (2026-07-07)

A later committed pass added `/assets-liabilities/:id` and `AccountDetailPage.vue`, with visual validation recorded in `VALIDATION.md` for budget account, investment account, and loan detail structures. This advances part of the detail-page scope before Work Item B, but the plan still lists Work Item B next because the Add item wizard and explicit add route do not exist yet.

### Work Item B Completion (2026-07-07)

Work Item B is complete. `/assets-liabilities/add` now renders a modal wizard over the Assets & Liabilities overview instead of falling through to the dynamic detail route. The first step aligns with mock 02: title, three-step progress rail, five entity-type row cards, the budget-boundary explainer, and the Aspire onboarding note. The second step collects minimal common and type-specific fields, then submits to the existing `POST /api/accounts` endpoint and routes to the created account detail page. Cypress coverage proves route safety, type selection, and the create-account payload; `DropdownButton` coverage proves the primary split-button click now emits an event for the Add item route.

### Work Item C Completion (2026-07-09)

Work Item C is complete for the budget-account detail scope. The existing `/assets-liabilities/:id` page now aligns more closely with mock 03: back navigation, clean account title/badges, direct Reconcile action, secondary More actions split button, kebab affordance, five metric cards, a dense budget-account ledger table with Memo and row action affordances, balance-over-time preview, Summary & notes panel, and sidebar cards for account details, reconciliation, history, and configuration. A new Cypress component spec covers the budget account route contract and verifies that only transactions from the target account are rendered from the fetched page. Browser validation captured desktop and narrow screenshots at `/home/ogle/src/dojo2/tmp/account-detail-workitem-c-desktop.png` and `/home/ogle/src/dojo2/tmp/account-detail-workitem-c-narrow.png`.

## Context and Orientation

The dojo frontend is a Vue 3 application in `web/src/dojo/`. Routes are defined in `web/src/dojo/router.ts`. Pages live in `web/src/dojo/pages/`. Shared components live in `web/src/dojo/components/` organized by area (actions, data, overlays, foundations, budget).

The backend already has:
- `GET /api/assets-liabilities` returning grouped cards with source_of_truth, value_minor, group_totals, asset/liability/net totals.
- `POST/PUT /api/accounts`, `GET /api/accounts`.
- Snapshot/valuation CRUD: positions, cash-snapshots, price-snapshots, tracking-snapshots, loan-snapshots, tangible-valuations.

Existing atoms available for reuse: Button, DropdownButton, PageHeader, MetricStrip, FormModal, LargeDetailModal, Tabs, SelectField, TextField, CurrencyField, DatePicker, KeyValueList, TableShell, StateBadge, NavigationRail, PersistentWarningBanner, HistoricalBanner, ProgressRing, Slider, RadioGroup, IconPicker, FullScreenTrouser.

The API client is in `web/src/dojo/api/client.ts` using vue-query for caching.

## Plan of Work

### Work Item A: Overview Page

1. Create `web/src/dojo/pages/AssetsLiabilitiesPage.vue` with:
   - PageHeader with title "Assets & Liabilities" + "Add item" primary action button
   - MetricStrip showing net worth, total assets, total liabilities, period change
   - Grouped stacked entity cards (CASH, INVESTMENTS, TANGIBLE_ASSETS, CREDIT, LOANS)
   - Each group rendered as full-width StackedEntityCard components

2. Create `web/src/dojo/components/data/StackedEntityCard.vue` as a new shared atom:
   - Props: name, primaryValue, icon, delta, metadata, status, trend, clickable, sourceOfTruth
   - Visual: metadata rail, current balance/valuation, period change, pending amount, source-of-truth chip, reconciliation freshness, attention state
   - Fixture file: `StackedEntityCard.fixtures.ts`
   - Manifest entry in `web/src/dojo/design-system/manifest.yaml`
   - Cypress component test

3. Add route `/assets-liabilities` to `web/src/dojo/router.ts`

4. Wire to `/api/assets-liabilities` endpoint using vue-query

### Work Item B: Add Item Wizard

1. Create wizard component (page-level composition, NOT cataloged)
2. Step 1: Choose entity type (budget account, tracking account, investment account, loan, tangible asset)
3. Step 2: Type-specific minimal form using existing form controls
4. Include SPEC-mandated "Need to bring in Aspire data? Use Onboarding." line

### Work Item C: EntityDetailLayout + Budget Account Detail

1. Create `EntityDetailLayout` shared component (catalog it):
   - Back link, header with name + type + badges
   - MetricStrip, primary activity table + right rail
   - Lower chart section, slot for centered modal
   - Reused across all five detail pages

2. Create budget account detail page:
   - Ledger-derived balance
   - Filtered transaction ledger scoped to the account
   - Reconciliation status
   - Edit configuration entry point

### Work Items D-H: Additional Detail Pages

(To be detailed as work progresses)

## Concrete Steps

Run commands from the repository root `/home/ogle/src/dojo2`.

For each work item:
1. Create/edit the necessary Vue components
2. Add fixtures for new shared components
3. Update manifest.yaml
4. Run `just lint-api`, `just typecheck`, `just format-check`
5. Run `just test-unit`, `just test-property`, `just test-integration`
6. Run `just test-web` for Cypress component tests
7. Run `just check` before claiming done

## Validation and Acceptance

Each work item is accepted when:
1. The page/component renders correctly at DESIGN.md breakpoints
2. API integration works (data loads, displays correctly)
3. All `just check` commands pass
4. Visual validation loop completed against mock screens
5. BATON.md updated

## Idempotence and Recovery

Steps can be repeated safely. Frontend changes are additive. If a component needs rework, delete and recreate.

## Artifacts and Notes

Mock screens available at: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/`

- 01-assets-liabilities-overview.png
- 02-add-item-type-wizard.png
- 03-budget-account-detail.png
- 04-tracking-account-upgrade-cutover.png
- 05-investment-account-detail.png
- 06-investment-contribution-modal.png
- 07-loan-detail-payment-modal.png
- 08-reconciliation-review.png (DEFERRED - Phase 9)

## Interfaces and Dependencies

- Frontend uses Vue 3 + vue-router + vue-query
- API client in `web/src/dojo/api/client.ts`
- Types in `web/src/dojo/types.ts`
- Design tokens from `web/src/dojo/design-system/tokens.css`
- Shared components in `web/src/dojo/components/`
