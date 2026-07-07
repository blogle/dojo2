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

## Work Item 1.1: Token System and Global Stylesheet

*Not yet completed.*

## Work Item 1.2: Contributor Documentation Update

*Not yet completed.*

## Work Item 6.A: Assets & Liabilities Overview Page

**Status**: Implementation complete, visual validation pending.

### Commands run

- `just lint-api` — Passed
- `just typecheck` — Passed
- `just format-check` — Passed (after running `just format`)

### Test results

- Backend: No backend changes made
- Frontend: Cypress component test created (`StackedEntityCard.cy.ts`), but Cypress not installed in environment

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

### Visual validation

- Mock screen: `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/01-assets-liabilities-overview.png`
- Status: Pending (need to run `just web` and compare visually)

### Validation gaps

- Cypress not installed, so component tests cannot be run
- Visual comparison not performed
- No backend integration tests (backend already has tests for `/api/assets-liabilities`)

---

*Add new work items above as they are completed.*
