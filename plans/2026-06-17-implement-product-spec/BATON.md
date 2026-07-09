# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 6 — Assets & Liabilities Frontend Flows

Current work-item status: **Not started — Work Item C (EntityDetailLayout + Budget Account Detail)**

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

## Current repository state

- **Branch**: `master`
- **Working tree**: Clean after commit `d27913b feat(onboarding): add import review flow`.
- **Last completed task**: Onboarding import review flow, Assets & Liabilities wizard remediation, import details modal fixes, and `/budgets` route-load fix.
- **Known failing checks**: None known. Latest post-fix checks run: `just typecheck`, `just lint-web`, and `cd web && pnpm test:component --spec "cypress/component/HierarchicalCategoryTable.cy.ts"` passed. Earlier in the same implementation pass, `just lint-api`, `just test-integration`, and `cd web && pnpm test:component --spec "cypress/component/OnboardingImportDetailsModal.cy.ts"` passed. Full `just check` was not rerun after the final lazy-draggable/Vite fix.
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
- Add item wizard at `/assets-liabilities/add` with type selection and minimal account creation forms. The overview header now uses a plain `Add item` button; direct type shortcuts are no longer exposed from the overview header.
- Onboarding import review flow that analyzes Aspire data, lets users review every net-worth category treatment, asks for simple low-confidence confirmation, then commits the reviewed import.
- Import details modal supports both legacy validation-report imports and review-based imports with imported-record counts and net-worth decision summaries.
- Budget page route loading is resilient to `vue-draggable-plus` optimized dependency load issues because draggable behavior is loaded only when reorder mode is enabled.

Frontend capabilities still planned:
- EntityDetailLayout extraction, if the detail-page implementation should become a shared component
- Richer detail pages for each account class beyond the current shared page shell

## Next work item

**Work Item C: EntityDetailLayout + Budget Account Detail**

### Objective

Create or extract a reusable `EntityDetailLayout` shared component and align the budget account detail page to the Work Item C contract. A preliminary `AccountDetailPage.vue` already exists, so this work item should reconcile that implementation with the plan instead of duplicating it.

### Scope

1. Inspect `web/src/dojo/pages/AccountDetailPage.vue` and decide whether to extract a shared `EntityDetailLayout` component now or document why the current page-local layout is sufficient for this iteration.
2. If extracting, create `web/src/dojo/components/data/EntityDetailLayout.vue` with a colocated fixture and manifest entry only if it meets catalog criteria.
3. Ensure the budget account detail page includes back navigation, name/type/badges, ledger-derived balance metrics, transaction ledger filtered or clearly scoped to the account, reconciliation status, account metadata, record history affordance, and edit configuration entry point.
4. Keep existing investment, loan, tracking, and tangible-asset rendering from regressing while budget-account detail is aligned.
5. Add focused tests for the detail route and budget-account detail behavior.
6. Confirm the latest onboarding import review and `/budgets` route-load fixes are not regressed by any detail-page imports or route changes.

### Non-scope

1. Do not implement reconciliation review workflows.
2. Do not add charting library integration.
3. Do not implement investment contribution, loan payment, tracking cutover, or tangible valuation flows beyond preserving existing placeholders.
4. Do not rewrite unrelated overview or wizard behavior.

### Guardrails

1. Use `SPEC.md` for product terminology and `DESIGN.md` tokens/components for visual decisions.
2. Avoid cataloging `EntityDetailLayout` unless it is truly reusable and fixtureable under the design-system rules.
3. Preserve route order: `/assets-liabilities/add` must remain before `/assets-liabilities/:id`.
4. Treat the current lack of server-side account filtering in `fetchTransactionsPage` as a known API gap unless this work item explicitly adds backend support.
5. `/budgets` must continue to load without requiring `vue-draggable-plus` during initial route resolution.

### Remaining tasks

1. Inspect current `AccountDetailPage.vue`, `AccountDetailPage` route behavior, and existing tests.
2. Decide whether to extract `EntityDetailLayout`; implement the smallest correct shape.
3. Align budget-account detail behavior and copy with `SPEC.md` and mock 03.
4. Add or update focused Cypress coverage.
5. Update `VALIDATION.md`, this ExecPlan, and this baton.
6. Run the narrow relevant Cypress coverage first, then `just test-web`, then `just check` before claiming done.
7. Commit changes in one concise Work Item C commit.

### Definition of done

1. `/assets-liabilities/:id` renders the budget account detail page correctly for budget accounts.
2. The page exposes the required budget-account detail information and actions listed in scope.
3. Any shared `EntityDetailLayout` extraction has fixtures, manifest entry, and Cypress coverage if cataloged.
4. Existing add wizard and overview routes still work.
5. `just check` passes.
6. Validation and baton updates are complete.

## Human decisions required

None.

## Known risks and observations

- The `StackedEntityCard` component uses simplified metadata display. May need enhancement for more complex entity types.
- The overview page currently shows all groups. May need filtering or sorting options in future.
- `fetchTransactionsPage` does not support account-id filtering; current detail-page transaction scoping may be incomplete for accounts with transactions outside the first fetched page.
- The latest onboarding import review work intentionally counts unique Aspire net-worth categories for decision summaries, not raw valuation rows.
- `vue-draggable-plus` is now a lazy dependency of `HierarchicalCategoryTable.vue`; tests that mount reorder mode may need Vite optimized-dependency prewarming, which is handled by `web/vite.config.ts`.

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
