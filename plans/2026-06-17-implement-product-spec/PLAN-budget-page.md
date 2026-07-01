# Budget Page Implementation Plan

## Goal

Build the complete budgets page across all 10 mock screens, including backend goal configuration support, vue-router integration, and full frontend assembly from existing design-system components.

## Scope Summary

- **Backend**: Add goal config columns to categories table (schema change, no migration — rebuild DB), goal config API endpoints, monthly_funding computation, unconfigured goal count
- **Frontend**: Create `BudgetsPage.vue`, wire vue-router, build goal editor, implement all 10 modal flows
- **10 mock screens**: Default, historical, add group, add category, reorder, category detail, funding negative, move funds, fund group, retired categories

## Key Simplification

No SCD2 migration needed. Blow away and rebuild the DuckDB database. New goal config columns are added to `current.sql` directly and start as NULL until configured through the UI.

## Reference Files

- Mock screens: `plans/2026-06-17-implement-product-spec/budget_screens/`
- SPEC.md budget section: lines 417-587
- DESIGN.md budget tokens: hierarchical-category-table, metric-strip, funding-dropdown sections
- Existing components: `web/src/dojo/components/` (34 components)
- State management: `web/src/dojo/state/app.ts`
- API client: `web/src/dojo/api/client.ts`
- Types: `web/src/dojo/types.ts`
- Backend service: `api/src/dojo/service.py`
- Backend routes: `api/src/dojo/api/routes.py`
- Schema: `api/src/dojo/sql/schema/current.sql`

---

## Phase 1: Backend — Goal Configuration

### 1.1 Add goal columns to categories table

**File**: `api/src/dojo/sql/schema/current.sql` (line 64-80)

Add four columns to the `categories` CREATE TABLE, after `due_date_rule`:

```sql
goal_type TEXT,
goal_amount_minor BIGINT,
goal_frequency TEXT,
goal_due_date DATE,
```

`goal_type` values: `ONE_TIME`, `RECURRING`, `DISCRETIONARY`, or NULL (unconfigured)
`goal_frequency` values: `MONTHLY`, `QUARTERLY`, `YEARLY`, or NULL

### 1.2 Update `create_category`

**File**: `api/src/dojo/service.py` (line 1379)

Add to `insert_version` call:
- `goal_type`: `payload.get("goal_type")`
- `goal_amount_minor`: `payload.get("goal_amount_minor")`
- `goal_frequency`: `payload.get("goal_frequency")`
- `goal_due_date`: `payload.get("goal_due_date")`

### 1.3 Update `update_category`

**File**: `api/src/dojo/service.py` (line 1420)

Add to `replace_current_version` call:
- `goal_type`: `payload.get("goal_type", current["goal_type"])`
- `goal_amount_minor`: `payload.get("goal_amount_minor", current["goal_amount_minor"])`
- `goal_frequency`: `payload.get("goal_frequency", current["goal_frequency"])`
- `goal_due_date`: `payload.get("goal_due_date", current["goal_due_date"])`

### 1.4 Add `compute_monthly_funding` to `list_categories`

**File**: `api/src/dojo/service.py`

After fetching each category (around line 950), compute `monthly_funding_minor`:

- `ONE_TIME`: `goal_amount_minor / max(1, months_until(goal_due_date))`
- `RECURRING`: `goal_amount_minor` if MONTHLY, `/3` if QUARTERLY, `/12` if YEARLY
- `DISCRETIONARY`: `goal_amount_minor` (direct monthly amount)
- NULL (unconfigured): `0`

Include `monthly_funding_minor` in each category dict response.

### 1.5 Add goal config endpoints

**File**: `api/src/dojo/api/routes.py`

- `GET /api/categories/{category_id}/goal` — returns `{ goal_type, goal_amount_minor, goal_frequency, goal_due_date, monthly_funding_minor }`
- `PUT /api/categories/{category_id}/goal` — updates goal fields via SCD2

**File**: `api/src/dojo/service.py`

- `get_category_goal(category_id)` — reads current goal config
- `update_category_goal(category_id, payload)` — SCD2 update of goal fields only

### 1.6 Add unconfigured goal count to budget response

**File**: `api/src/dojo/service.py` (line 1004, `get_budget`)

Add to response:
```python
"unconfigured_goal_count": sum(
    1 for c in categories
    if c["category_kind"] == CATEGORY_KIND_STANDARD and c["goal_type"] is None
),
```

### 1.7 Verify DB rebuild works

- Delete existing DuckDB file
- Run `just setup` to reprovision
- Run `just check` to verify backend tests pass
- Verify import still works (categories created with NULL goal columns)

---

## Phase 2: Frontend — Routing & Page Shell

### 2.1 Add vue-router

vue-router is already in `package.json`.

**File**: `web/src/dojo/router.ts` (new)

```typescript
import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/dev/design-system",
      component: () => import("./pages/DesignSystemPage.vue"),
    },
    {
      path: "/",
      component: () => import("./pages/BudgetsPage.vue"),
    },
    {
      path: "/budgets",
      component: () => import("./pages/BudgetsPage.vue"),
    },
  ],
});

export default router;
```

**File**: `web/src/main.ts` — add `app.use(router)` after `createApp(App)`

**File**: `web/src/dojo/App.vue` — replace if/else with `<router-view />`

**File**: `web/cypress/component/App.cy.ts` — update test for routing

### 2.2 Currency formatting utility

**File**: `web/src/dojo/utils/currency.ts` (new)

```typescript
export function formatCurrency(minor: number): string {
  const abs = Math.abs(minor) / 100;
  const formatted = abs.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return minor < 0 ? `-$${formatted}` : `$${formatted}`;
}

export function formatDelta(from: number, to: number): string {
  return `${formatCurrency(from)} → ${formatCurrency(to)}`;
}
```

### 2.3 BudgetsPage shell

**File**: `web/src/dojo/pages/BudgetsPage.vue` (new)

Layout (matching mock 01):

```
NavigationRail (brand="dojo", items=[Home, Budget(current), Transactions, Assets, Settings])
├── PersistentWarningBanner (if unconfigured_goal_count > 0)
├── HistoricalBanner (if isHistorical)
├── PageHeader (title="Budget", actions slot)
│   ├── DropdownButton (Add → "Add category", "Add category group")
│   ├── Button (Reorder)
│   └── Button (Retired categories)
├── MetricStrip (Month, Available to budget, Activity, Budgeted)
├── ReorderModeBanner (when isReordering)
├── HierarchicalCategoryTable (expandable, columns, rows)
├── FormModal (Add category group)
├── FormModal (Add category — with GoalEditor)
├── CategoryDetailModal (category detail)
├── GroupFundingModal (fund group)
├── FormModal (Move funds)
├── LargeDetailModal (Retired categories)
└── PersistentWarningBanner (negative ATB)
```

State (all local refs, reading from `useAppState()`):
- `selectedMonth` — synced with MetricStrip month selector
- `isReordering` — toggle for reorder mode
- `reorderChanges` — pending reorder operations
- `activeModal` — which modal is open (null | 'add-group' | 'add-category' | 'category-detail' | 'fund-group' | 'move-funds' | 'retired')
- `selectedCategory` / `selectedGroup` — for detail/funding modals
- `isHistorical` — computed: `selectedMonth !== currentMonth`

### 2.4 Data transformation to table rows

Transform `CategoryGroup[]` into `HierarchicalCategoryRow[]`:

```typescript
function toTableRows(groups: CategoryGroup[]): HierarchicalCategoryRow[] {
  return groups.map(group => ({
    key: group.group_id,
    label: group.name,
    icon: groupIconForKind(group),
    group: true,
    cells: {
      goal: "—",
      dueDate: "—",
      available: formatCurrency(group.totals.available_minor),
      activity: formatCurrency(group.totals.month_activity_minor),
      budgeted: formatCurrency(group.totals.month_budgeted_minor),
    },
    children: group.categories.map(cat => ({
      key: cat.category_id,
      label: cat.name,
      cells: {
        goal: cat.goal_type ? formatCurrency(cat.goal_amount_minor) : "—",
        dueDate: formatGoalDueDate(cat),
        available: formatCurrency(cat.available_minor),
        activity: formatCurrency(cat.month_activity_minor),
        budgeted: formatCurrency(cat.month_budgeted_minor),
      },
      cellVariants: computeVariants(cat),
      states: computeStates(cat),
    })),
  }));
}
```

---

## Phase 3: Frontend — Goal Editor Component

### 3.1 GoalEditor component

**File**: `web/src/dojo/components/budget/GoalEditor.vue` (new)

Props:
```typescript
{
  goalType: string | null,         // "ONE_TIME" | "RECURRING" | "DISCRETIONARY" | null
  goalAmountMinor: number | null,
  goalFrequency: string | null,    // "MONTHLY" | "QUARTERLY" | "YEARLY" | null
  goalDueDate: string | null,      // ISO date string
  monthlyFundingMinor: number,     // computed, read-only
  disabled?: boolean,
}
```

Layout (matching mock 04):
- Label: "Goal" with helper "Set a goal and schedule for this category."
- RadioGroup: "One-time goal", "Recurring goal", "Discretionary goal"
- Conditional fields:
  - ONE_TIME: CurrencyField (goal amount) + DatePicker (goal date)
  - RECURRING: CurrencyField (amount per occurrence) + SelectField (Frequency) + DatePicker (next due date) + read-only monthly funding display
  - DISCRETIONARY: CurrencyField (monthly goal)
- Emits: `update:goalType`, `update:goalAmountMinor`, `update:goalFrequency`, `update:goalDueDate`

---

## Phase 4: Frontend — Add Modals (Screens 03, 04)

### 4.1 Add Category Group modal (mock 03)

Inside BudgetsPage.vue. Triggered by DropdownButton `select("add-group")`.

- FormModal, title "Add category group"
- TextField: "Group name" (required), helper "Empty category groups are valid. You can add categories later."
- On submit: `saveCategoryGroup({ name })`, close modal

### 4.2 Add Category modal (mock 04)

Inside BudgetsPage.vue. Triggered by DropdownButton `select("add-category")`.

- FormModal, title "Add category"
- SelectField: "Parent group" with helper "Choose where this category belongs."
- GoalEditor component inline
- Monthly funding read-only display
- On submit: `saveCategory({ group_id, name, goal_type, goal_amount_minor, goal_frequency, goal_due_date })`, close modal

---

## Phase 5: Frontend — Category Detail Modal (Screen 06)

### 5.1 CategoryDetailModal component

**File**: `web/src/dojo/components/budget/CategoryDetailModal.vue` (new)

Props:
```typescript
{
  visible: boolean,
  category: Category | null,
}
```

Layout (matching mock 06):
- Header: category icon + name + close button
- Summary metrics: Current available, Monthly goal, Budgeted this month, Activity this month
- Tabs (Overview, Funding history, Spending history, Advanced allocation)
- Overview tab: Goal config panel (KeyValueList), Goal progress (ProgressRing), Funding to date
- Funding actions: Fund dropdown + Move funds button + Edit config button
- Footer: Close button

### 5.2 FundingOptionSelector component

**File**: `web/src/dojo/components/budget/FundingOptionSelector.vue` (new)

Custom dropdown with funding shortcuts:
- "Fund up to next month — $X.XX"
- "Fund to monthly goal — $X.XX"
- "Custom amount..." with inline CurrencyField

Emits: `fund(amount_minor)`

### 5.3 Preview section

PreviewBox showing: amount being funded, category balance before→after, ATB before→after, negative ATB warning if applicable.

---

## Phase 6: Frontend — Funding Flows (Screens 07, 08, 09)

### 6.1 Negative ATB warning (mock 07)

PersistentWarningBanner when `state.budget.available_to_budget_minor < 0`:
- Title: "Your Available to budget is negative. Add funds or make changes to your budget to fix this."
- Primary: "Learn more", Dismissable
- Also: MetricStrip ATB value in red

### 6.2 Move Funds modal (mock 08)

**File**: `web/src/dojo/components/budget/MoveFundsEditor.vue` (new)

FormModal with: From category select, To category select, Amount CurrencyField, Preview section showing both categories' balance changes, Cancel/Save.

On save: `submitAllocation({ from_bucket_id, to_bucket_id, amount_minor, path: '/api/allocations/move' })`

### 6.3 Fund Category Group modal (mock 09)

**File**: `web/src/dojo/components/budget/GroupFundingModal.vue` (new)

LargeDetailModal, two-column layout:
- Left: Source of money, funding summary table, amount slider
- Right: ATB preview, per-category preview with ProgressBars, legend
- On submit: process categories in priority order via `submitAllocation`

---

## Phase 7: Frontend — Reordering Mode (Screen 05)

In BudgetsPage.vue:
- Toggle via "Reorder" button
- Show ReorderModeBanner with pending count
- Pass `reorderable=true` to HierarchicalCategoryTable
- Disable Add/Retired buttons
- Track changes locally, batch update sort_order on save

---

## Phase 8: Frontend — Historical Mode (Screen 02)

In BudgetsPage.vue:
- Month ≠ current → isHistorical
- Show HistoricalBanner with "Return to current"
- Disable all action buttons, modals, table selection

---

## Phase 9: Frontend — Retired Categories (Screen 10)

LargeDetailModal with search, grouped table of hidden categories, Restore buttons, summary footer. Data from `fetchCategories(month, showHidden=true)` filtered to `is_hidden`.

---

## Phase 10: Cypress Tests

### BudgetsPage tests

**File**: `web/cypress/component/BudgetsPage.cy.ts` (new)

1. Renders nav, metrics, table
2. Correct metrics from API
3. Add dropdown options
4. Add group modal flow
5. Add category modal with goal editor
6. Category row opens detail modal
7. Detail modal tabs and funding actions
8. Reorder mode toggle/banner/drag
9. Retired categories modal flow
10. Historical mode banner/disabled actions
11. Negative ATB warning
12. Move funds modal flow
13. Fund group modal flow

### GoalEditor tests

**File**: `web/cypress/component/GoalEditor.cy.ts` (new)

1. Empty state
2. One-time fields
3. Recurring fields + monthly funding
4. Discretionary fields
5. Emits updates
6. Disabled state

---

## Verification

After each phase:
1. `just lint-web` — no new warnings
2. `just typecheck` — no type errors
3. `just test-web` — all existing + new tests pass
4. `just check` — full repo verification

Phase-specific:
- Phase 1: `just api` starts, GET /api/budget returns `unconfigured_goal_count`, goal endpoints work
- Phase 2: App boots at `/`, budget page renders with nav rail
- Phases 3-9: Each modal/flow renders per mock screen
- Phase 10: All Cypress tests green

---

## File Summary

### New files (backend)
- `api/src/dojo/sql/schema/current.sql` — modified: add goal columns
- `api/src/dojo/service.py` — modified: goal config CRUD, monthly_funding, unconfigured count
- `api/src/dojo/api/routes.py` — modified: goal config endpoints

### New files (frontend)
- `web/src/dojo/router.ts`
- `web/src/dojo/pages/BudgetsPage.vue`
- `web/src/dojo/utils/currency.ts`
- `web/src/dojo/components/budget/GoalEditor.vue`
- `web/src/dojo/components/budget/CategoryDetailModal.vue`
- `web/src/dojo/components/budget/FundingOptionSelector.vue`
- `web/src/dojo/components/budget/MoveFundsEditor.vue`
- `web/src/dojo/components/budget/GroupFundingModal.vue`
- `web/cypress/component/BudgetsPage.cy.ts`
- `web/cypress/component/GoalEditor.cy.ts`

### Modified files
- `web/src/main.ts` — add `app.use(router)`
- `web/src/dojo/App.vue` — replace if/else with `<router-view>`
- `web/cypress/component/App.cy.ts` — update for routing
