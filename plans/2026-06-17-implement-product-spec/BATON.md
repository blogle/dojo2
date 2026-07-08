# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 6 — Assets & Liabilities Frontend Flows

Current work-item status: **Not started — Work Item B (Add Item Wizard)**

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

## Current repository state

- **Branch**: `master`
- **Working tree**: Tracked files clean before this baton refresh; untracked local artifacts exist (`PROMPT-assets-liabilities.md`, `PROMPT-visual-gaps.md`, `tmp/`) and were not created or modified for this baton update.
- **Last completed task**: Work Item A overview page plus committed detail-page visual gap closure.
- **Known failing checks**: None. `just test-web` passes on latest rerun with 247 tests; `just check` passes after this baton refresh.
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

Frontend capabilities still planned:
- Add item wizard and explicit `/assets-liabilities/add` route
- EntityDetailLayout extraction, if the detail-page implementation should become a shared component
- Richer detail pages for each account class beyond the current shared page shell

## Next work item

**Work Item B: Add Item Wizard**

### Objective

Create the Add item wizard for Assets & Liabilities so users can choose an entity type and begin adding a budget account, tracking account, investment account, loan, or tangible asset.

### Scope

1. Add an explicit `/assets-liabilities/add` route before `/assets-liabilities/:id` in `web/src/dojo/router.ts`.
2. Create a page-level wizard component under `web/src/dojo/pages/` or a page-local component directory; do not catalog it unless it becomes a reusable shared primitive.
3. Step 1 selects the entity type: budget account, tracking account, investment account, loan, tangible asset.
4. Step 2 presents the minimal type-specific form using existing form components where possible.
5. Include the SPEC-mandated copy: "Need to bring in Aspire data? Use Onboarding."
6. Preserve the established NavigationRail/PageHeader/MetricStrip visual language from the overview page.

### Non-scope

1. Do not infer rich investment, loan, or tangible-asset entities from Aspire net-worth categories.
2. Do not add reconciliation review flows.
3. Do not add charting or historical time-travel behavior.
4. Do not create a new shared wizard component unless repeated use becomes concrete in this work item.

### Guardrails

1. Use `SPEC.md` for product terminology and `DESIGN.md` tokens/components for visual decisions.
2. Keep the route order safe: `/assets-liabilities/add` must not fall through to `/assets-liabilities/:id`.
3. Use existing API client patterns and vue-query mutation patterns where available.
4. Keep changes local to the wizard and required API/type wiring.

### Remaining tasks

1. Inspect existing account create/edit APIs and frontend form components.
2. Add the explicit add route and wizard page.
3. Wire type-specific submit paths to existing backend capabilities where they already exist.
4. Add focused tests for route rendering and wizard type selection.
5. Update `VALIDATION.md`, this ExecPlan, and this baton.
6. Run `just test-web`, then `just check` before claiming done.
7. Commit changes in one concise Work Item B commit.

### Definition of done

1. `/assets-liabilities/add` renders a wizard instead of the account detail page for id `add`.
2. The wizard lets users select each supported entity type.
3. The wizard shows the SPEC-mandated Aspire onboarding guidance.
4. Type-specific forms use existing design-system components and submit to existing backend endpoints where supported.
5. Returning/canceling from the wizard lands back on `/assets-liabilities` without losing the main page state.
6. `just check` passes.
7. Validation and baton updates are complete.

## Human decisions required

None.

## Known risks and observations

- The `StackedEntityCard` component uses simplified metadata display. May need enhancement for more complex entity types.
- The overview page currently shows all groups. May need filtering or sorting options in future.
- The "Add item" dropdown routes to `/assets-liabilities/add?type=...`, but no explicit add route exists yet. Because `/assets-liabilities/:id` exists, the add URL can currently be treated as a detail page for id `add`; Work Item B should fix this first.

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
