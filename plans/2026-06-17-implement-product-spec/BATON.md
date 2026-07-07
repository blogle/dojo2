# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 6 — Assets & Liabilities Frontend Flows

Current work-item status: **In Progress — Work Item A (Overview Page)**

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
- (2026-07-07) Work Item A (Overview Page) — In Progress:
  - Created `StackedEntityCard.vue` shared component with fixtures and manifest entry.
  - Created `AssetsLiabilitiesPage.vue` with PageHeader, MetricStrip, grouped stacked entity cards.
  - Added `/assets-liabilities` route to router.
  - Added `fetchAssetsLiabilities` API client function.
  - Updated types with `AssetsLiabilitiesResponse` and `AssetsLiabilitiesItem`.
  - Updated navigation in BudgetsPage and TransactionsPage to link to `/assets-liabilities`.

## Current repository state

- **Branch**: Not specified
- **Working tree**: Modified (frontend changes for Work Item A)
- **Last completed task**: Work Item A partial implementation
- **Known failing checks**: None (lint, typecheck, format-check pass)
- **Required services**: DuckDB (provisioned by `just api`), Google OAuth (optional)
- **Feature flags**: None
- **Aspire data**: Deterministic fixture available at `fixture://default`

## Capability and dependency status

Backend capabilities already exist:
- `GET /api/assets-liabilities` returns grouped cards with source_of_truth, value_minor, group_totals, asset/liability/net totals.
- `POST/PUT /api/accounts`, `GET /api/accounts`.
- Snapshot/valuation CRUD: positions, cash-snapshots, price-snapshots, tracking-snapshots, loan-snapshots, tangible-valuations.

Frontend capabilities being built:
- Overview page with `/assets-liabilities` route
- StackedEntityCard shared component
- EntityDetailLayout (planned)
- Detail pages for each account class (planned)

## Next work item

**Complete Work Item A: Overview Page**

### Remaining tasks

1. Run Cypress component test for StackedEntityCard
2. Visual validation loop against mock screen 01-assets-liabilities-overview.png
3. Update VALIDATION.md with visual-loop paragraph
4. Update ExecPlan progress section
5. Commit changes

### Definition of done

1. `/assets-liabilities` route renders correctly
2. MetricStrip shows net worth, total assets, total liabilities
3. Grouped stacked entity cards display correctly
4. Navigation rail includes Assets & Liabilities link
5. `just check` passes
6. Visual validation completed

## Human decisions required

None.

## Known risks and observations

- The `StackedEntityCard` component uses simplified metadata display. May need enhancement for more complex entity types.
- The overview page currently shows all groups. May need filtering or sorting options in future.
- The "Add item" button routes to `/assets-liabilities/add` but that route doesn't exist yet (Work Item B).

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
