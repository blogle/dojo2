# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 6 — Assets & Liabilities Frontend Flows

Current work-item status: **Not started — Work Item D (Tracking Account Detail + Cutover Modal)**

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

## Current repository state

- **Branch**: `master`
- **Working tree**: Clean after commit `feat(assets-liabilities): align budget account detail`.
- **Last completed task**: Work Item C budget-account detail alignment, focused Cypress coverage, visual validation, and SQL-boundary cleanup required by `just check`.
- **Known failing checks**: None known. Latest checks run: `just typecheck`, `just lint-web`, `cd web && pnpm test:component --spec "cypress/component/AccountDetailPage.cy.ts"`, `just test-web`, and `just check` all passed. The first `just check` attempt surfaced API format drift and import-draft inline SQL policy violations; `just format` and SQL file extraction resolved them.
- **Required services**: DuckDB (provisioned by `just api`), Google OAuth (optional)
- **Feature flags**: None
- **Aspire data**: Deterministic fixture available at `fixture://default`

## Capability and dependency status

Backend capabilities already exist:
- `GET /api/assets-liabilities` returns grouped cards with source_of_truth, value_minor, group_totals, asset/liability/net totals.
- `POST/PUT /api/accounts`, `GET /api/accounts`.
- Snapshot/valuation CRUD: positions, cash-snapshots, price-snapshots, tracking-snapshots, loan-snapshots, tangible-valuations.

Frontend capabilities now present:
- Overview page with `/assets-liabilities` route
- StackedEntityCard shared component
- Account detail page at `/assets-liabilities/:id` with budget, investment, loan, tracking, and tangible-asset type handling
- Budget-account detail page now exposes mock-03-aligned header actions, metrics, scoped transaction table, chart/summary area, reconciliation/history/configuration affordances, and responsive narrow rendering.
- Add item wizard at `/assets-liabilities/add` with type selection and minimal account creation forms. The overview header now uses a plain `Add item` button; direct type shortcuts are no longer exposed from the overview header.
- Onboarding import review flow that analyzes Aspire data, lets users review every net-worth category treatment, asks for simple low-confidence confirmation, then commits the reviewed import.
- Import details modal supports both legacy validation-report imports and review-based imports with imported-record counts and net-worth decision summaries.
- Budget page route loading is resilient to `vue-draggable-plus` optimized dependency load issues because draggable behavior is loaded only when reorder mode is enabled.

Frontend capabilities still planned:
- Tracking account detail page with snapshot history and replacement/cutover affordance
- Richer investment, loan, tracking, and tangible-asset flows beyond the current shared page shell

## Next work item

**Work Item D: Tracking Account Detail + Cutover Modal**

### Objective

Align tracking-account detail behavior with SPEC.md and mock 04. The current `AccountDetailPage.vue` has a generic tracking branch, but it does not yet expose snapshot history, add/edit snapshot affordances, replacement/cutover state, or the cutover modal pattern shown in the mock.

### Scope

1. Inspect the existing tracking branch in `web/src/dojo/pages/AccountDetailPage.vue` and the current snapshot/valuation API client capabilities.
2. Align tracking detail copy and structure with SPEC.md: latest snapshot value, snapshot history, add/edit snapshot affordance, replacement or cutover affordance, and retired/replaced state when available.
3. Use mock 04 (`assets_liabilities_screens/04-tracking-account-upgrade-cutover.png`) to validate the cutover modal structure while avoiding non-scoped backend/domain work.
4. Preserve the Work Item C budget-account detail layout and do not regress add wizard or overview routes.
5. Add focused Cypress coverage for tracking-account detail rendering and cutover modal opening/closing.
6. Keep `EntityDetailLayout` uncataloged unless the tracking work creates a genuinely reusable, fixtureable shared component contract.

### Non-scope

1. Do not implement actual tracking-account replacement persistence or rich account backfill.
2. Do not add charting library integration.
3. Do not implement reconciliation review workflows.
4. Do not rewrite unrelated overview, wizard, budget-account, investment, loan, or tangible-asset behavior.

### Guardrails

1. Use `SPEC.md` for product terminology and `DESIGN.md` tokens/components for visual decisions.
2. Avoid cataloging any tracking detail layout or `EntityDetailLayout` unless it is truly reusable and fixtureable under the design-system rules.
3. Preserve route order: `/assets-liabilities/add` must remain before `/assets-liabilities/:id`.
4. Treat the current lack of server-side account filtering in `fetchTransactionsPage` as a known API gap unless this work item explicitly adds backend support.
5. `/budgets` must continue to load without requiring `vue-draggable-plus` during initial route resolution.

### Remaining tasks

1. Inspect current tracking detail rendering and available API fields for tracking snapshots/valuations.
2. Align tracking detail behavior and copy with `SPEC.md` and mock 04.
3. Add or update focused Cypress coverage.
4. Run browser visual validation for mock 04 and record screenshots/results in `VALIDATION.md`.
5. Update `PLAN-assets-liabilities-frontend.md`, `VALIDATION.md`, and this baton.
6. Run the narrow relevant Cypress coverage first, then `just test-web`, then `just check` before claiming done.
7. Commit changes in one concise Work Item D commit.

### Definition of done

1. `/assets-liabilities/:id` renders tracking-account details correctly for tracking accounts.
2. The page exposes latest snapshot value, snapshot history, add/edit snapshot affordance, replacement/cutover affordance, record history, and edit configuration entry point.
3. The cutover modal matches the mock 04 structure closely enough for the current non-persistence scope.
4. Existing budget-account detail, add wizard, and overview routes still work.
5. `just check` passes.
6. Validation and baton updates are complete.

## Human decisions required

None.

## Known risks and observations

- The `StackedEntityCard` component uses simplified metadata display. May need enhancement for more complex entity types.
- The overview page currently shows all groups. May need filtering or sorting options in future.
- `fetchTransactionsPage` does not support account-id filtering; current detail-page transaction scoping is limited to transactions returned by the current fetched page.
- The latest onboarding import review work intentionally counts unique Aspire net-worth categories for decision summaries, not raw valuation rows.
- `vue-draggable-plus` is now a lazy dependency of `HierarchicalCategoryTable.vue`; tests that mount reorder mode may need Vite optimized-dependency prewarming, which is handled by `web/vite.config.ts`.
- Work Item C required mechanical formatting in several files and SQL-boundary cleanup to satisfy `just check`; avoid undoing these when starting Work Item D.

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
