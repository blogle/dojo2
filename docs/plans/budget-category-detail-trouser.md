# Budget Category Detail: Full-Screen Trouser and Funding Modal Refactor

## Purpose

This ExecPlan refactors the budget category detail view from a centered modal to a full-screen trouser (right-side overlay panel), simplifies the funding flow from a split-button dropdown to a button-opens-modal pattern, and aligns the implementation with the mock screens in `plans/2026-06-17-implement-product-spec/budget_screens/`. After this change, clicking a category opens a full-screen trouser with overview, funding history, and spending history tabs; the Fund, Move funds, and Edit configuration actions are consistent button-opens-modal patterns; and the SPEC.md reflects these design decisions.

## Progress

- [ ] Create `FullScreenTrouser.vue` overlay component
- [ ] Refactor `CategoryDetailModal.vue` to use trouser layout with action buttons at top
- [ ] Create `FundingModal.vue` for funding a single category
- [ ] Wire `BudgetsPage.vue` to new components and modal state
- [ ] Update SPEC.md budget section to reflect trouser and funding modal changes
- [ ] Run `just check` to verify no regressions

## Surprises & Discoveries

- The current `CategoryDetailModal.vue` uses `LargeDetailModal` (max 900px centered modal) which is too narrow for the content-rich category detail view shown in mock 06.
- The mock 06 shows "Fund" as a split-button dropdown, but the user explicitly wants it simplified to a plain button that opens a modal, consistent with Move funds and Edit configuration.
- Mock 07 shows the funding modal with tabs (Details, Activity, Funding), but the user says those tabs are unnecessary since that data lives in the trouser. The funding modal should be a simple form with preview.
- The "Advanced allocation" tab in mock 06 is not needed per user direction.
- "Move funds" and "Edit configuration" in the mock appear in surface containers (cards), but the user wants them as plain buttons at the top of the trouser without containers.

## Decision Log

- Decision: Use a full-screen trouser (right-side overlay) instead of a centered modal for category detail.
  Rationale: The category detail view has substantial content (goal config, progress ring, funding to date, action buttons, allocation history) that benefits from full-viewport width. The user explicitly requested this.
  Date: 2026-07-01

- Decision: Simplify Fund from split-button dropdown to button-opens-modal.
  Rationale: User wants consistency across all actions (Fund, Move funds, Edit configuration) — each opens a modal with preview and confirmation. The dropdown pattern is being retired.
  Date: 2026-07-01

- Decision: Funding modal has no tabs.
  Rationale: The user states that detail/activity data lives in the trouser, not in the funding modal. The modal should be a focused funding form with preview.
  Date: 2026-07-01

- Decision: Remove "Advanced allocation" tab from category detail.
  Rationale: User direction. Allocation records are available from an Advanced section per SPEC, but the user does not want it as a tab in the current implementation.
  Date: 2026-07-01

- Decision: Move funds and Edit configuration are plain buttons without surface containers.
  Rationale: User wants these actions at the top of the trouser without card/surface wrappers, keeping the layout clean and consistent.
  Date: 2026-07-01

## Context and Orientation

The budget page lives in `web/src/dojo/pages/BudgetsPage.vue`. Category detail is currently handled by `web/src/dojo/components/budget/CategoryDetailModal.vue`, which wraps `LargeDetailModal` (a centered 900px modal). The funding dropdown is defined in `DESIGN.md` as a split-button component but is not yet implemented as a standalone component — the current `CategoryDetailModal` has placeholder tabs.

Key files:
- `web/src/dojo/pages/BudgetsPage.vue` — main budget page, manages modal state
- `web/src/dojo/components/budget/CategoryDetailModal.vue` — category detail (to be refactored)
- `web/src/dojo/components/budget/GoalEditor.vue` — goal configuration editor (reused)
- `web/src/dojo/components/budget/MoveFundsModal.vue` — move funds modal (existing)
- `web/src/dojo/components/budget/FundGroupModal.vue` — fund group modal (existing)
- `web/src/dojo/components/overlays/LargeDetailModal.vue` — large modal base (existing, still used elsewhere)
- `web/src/dojo/components/overlays/FormModal.vue` — form modal base (existing)
- `web/src/dojo/components/actions/Button.vue` — button component (existing)
- `web/src/dojo/components/navigation/Tabs.vue` — tabs component (existing)
- `web/src/dojo/composables/useDismissableLayer.ts` — dismiss logic (existing)
- `web/src/dojo/types.ts` — type definitions
- `web/src/dojo/state/app.ts` — app state management
- `SPEC.md` — product spec (lines 417-587 for budget section)
- `plans/2026-06-17-implement-product-spec/budget_screens/` — mock screens

## Plan of Work

### Step 1: Create `FullScreenTrouser.vue`

**File**: `web/src/dojo/components/overlays/FullScreenTrouser.vue` (new)

A full-screen overlay panel that slides in from the right. It covers the full viewport height and most of the width (leaving a narrow strip of the page visible on the left, similar to how the mocks show the category detail overlaying the budget table).

Props:
- `visible: boolean` — show/hide
- `title?: string` — panel title
- `subtitle?: string` — panel subtitle

Slots:
- `default` — main content body
- `tabs` — tab navigation area (rendered between header and body)
- `header-actions` — action buttons area (rendered in header, right side before close)
- `footer` — optional footer

Structure:
- Scrim overlay (same as LargeDetailModal, using `useDismissableLayer`)
- Panel element: `position: fixed; inset: 0; width: min(100%, 960px); margin-left: auto;` (right-aligned, leaving nav rail visible)
- Header with title, subtitle, header-actions slot, close button
- Tabs slot area
- Scrollable body
- Optional footer

The panel should use the same animation pattern as LargeDetailModal (opacity + translateY 200ms). The scrim covers the full viewport. The panel is right-aligned and takes up to 960px width.

### Step 2: Refactor `CategoryDetailModal.vue`

**File**: `web/src/dojo/components/budget/CategoryDetailModal.vue` (modify)

Replace `LargeDetailModal` with `FullScreenTrouser`. Restructure the layout to match mock 06.

New structure:
- **Header**: Category icon + name + group name subtitle
- **Header actions**: Fund button (primary), Move funds button (secondary), Edit configuration button (secondary) — these are plain buttons, no surface containers
- **Tabs**: Overview, Funding history, Spending history (remove Advanced allocation and Goals tabs)
- **Overview tab content**:
  - Summary metrics row: Current available, Monthly goal, Budgeted this month, Activity this month
  - Goal configuration panel (KeyValueList showing goal type, monthly goal, start month, target amount, target date, rollover, incremental)
  - Goal progress panel (ProgressRing with percentage, available, remaining, monthly goal)
  - Funding to date panel (expected funding, actual funding, deviation, additional monthly funding needed, spending reduction needed)
- **Funding history tab**: Placeholder text "Funding history — filtered view of category allocations" (actual table integration is future work)
- **Spending history tab**: Placeholder text "Spending history — filtered view of transactions" (actual table integration is future work)
- **Footer**: Close button

The Fund button emits an event `fund` that the parent (BudgetsPage) handles by opening the FundingModal. The Move funds button emits `move-funds`. The Edit configuration button emits `edit-config`.

Remove the `updateGoal` emit and the Goals/Funding tab content from this component — goal editing moves to a separate flow triggered by Edit configuration.

### Step 3: Create `FundingModal.vue`

**File**: `web/src/dojo/components/budget/FundingModal.vue` (new)

A simple form modal for funding a single category. Based on mock 07 but without tabs.

Props:
- `visible: boolean`
- `category: Category | null`

Slots/events:
- `close` — close modal
- `submit` — emit `{ categoryId: string, amountMinor: number }`

Content:
- Header: Category name + monthly goal subtitle
- "Fund [Category]" heading with helper text "Choose a funding shortcut or enter a custom amount."
- Funding option selector (custom dropdown or radio-like selector):
  - "Fund up to next month — $X.XX" (computed from category available and monthly goal)
  - "Fund to monthly goal — $X.XX" (computed from monthly goal minus current available)
  - "Custom amount..." with inline CurrencyField
- Preview section (boxed, with heading "Preview" and helper "Review the results of this action before you save."):
  - Amount being funded
  - Category balance before → after
  - Available to budget before → after
  - Warning message if ATB will be negative after funding
- Footer: Cancel button, Save button (primary)

Uses `FormModal` as the base overlay (480px max-width, centered).

### Step 4: Wire `BudgetsPage.vue`

**File**: `web/src/dojo/pages/BudgetsPage.vue` (modify)

Changes:
- Add `activeModal` values: `'funding'` (new), keep existing ones
- Add `fundingCategory` ref for the category being funded
- Import `FundingModal` component
- Update `handleRowSelect` to open the trouser for categories (keep fund-group for groups)
- Add handlers for events from CategoryDetailModal:
  - `@fund` → set fundingCategory, set activeModal to 'funding'
  - `@move-funds` → set activeModal to 'move-funds' (pre-select the current category as source)
  - `@edit-config` → open edit configuration flow (for now, log or placeholder)
- Add `submitFundCategory` handler that calls `saveCategory` with updated available_minor
- Add FundingModal to template
- Fix the "Review categories" button on the unconfigured goals warning — it currently opens retired modal, should open a category review flow (for now, keep as-is or point to a placeholder)

### Step 5: Update SPEC.md

**File**: `SPEC.md` (modify, lines ~502-587)

Update the budget section to reflect:
- Category and group detail uses a full-screen trouser (right-side overlay panel) instead of a centered modal
- The trouser contains Overview, Funding history, and Spending history tabs
- Funding history shows a filtered view of category allocations
- Spending history shows a filtered view of transactions
- Fund, Move funds, and Edit configuration are button actions at the top of the trouser
- Fund opens a dedicated modal with funding shortcuts, preview, and confirmation
- The fund modal does not contain detail or activity tabs
- Remove reference to "Advanced allocation records" as a tab in the category detail modal
- Allocation records remain available from an Advanced section per existing spec

## Concrete Steps

1. Create `web/src/dojo/components/overlays/FullScreenTrouser.vue` with the spec above
2. Modify `web/src/dojo/components/budget/CategoryDetailModal.vue` to use FullScreenTrouser, restructure tabs and layout
3. Create `web/src/dojo/components/budget/FundingModal.vue` with funding shortcuts and preview
4. Modify `web/src/dojo/pages/BudgetsPage.vue` to wire new components and modal state
5. Update SPEC.md lines 502-587 to reflect the new design
6. Run `just check` from repo root

## Validation and Acceptance

After implementation:
1. `just check` passes (lint, typecheck, tests)
2. Navigate to Budget page, click a category row → FullScreenTrouser opens from the right
3. Trouser shows category name, summary metrics, Overview/Funding history/Spending history tabs
4. Overview tab shows goal config, progress ring, funding to date
5. Fund button in header opens FundingModal with shortcut options and preview
6. Move funds button opens MoveFundsModal
7. Close button and scrim click close the trouser
8. FundingModal preview shows correct amounts and negative ATB warning when applicable
9. All existing budget page functionality still works (add group, add category, reorder, retired categories, fund group)

## Idempotence and Recovery

All steps are additive or modify existing files. No destructive operations. If a step fails, the previous steps can be retried. The `just check` command validates the full state.

## Artifacts and Notes

- Mock 06 (`06-category-detail-fund-dropdown.png`) shows the target layout for the category detail trouser
- Mock 07 (`07-funding-shortcuts-negative-preview.png`) shows the target layout for the funding modal (without tabs)
- Mock 08 (`08-move-funds-modal.png`) shows the existing Move funds modal layout (unchanged)
- The term "trouser" refers to a full-screen right-side overlay panel, distinct from a centered modal

## Interfaces and Dependencies

- `FullScreenTrouser.vue` uses `useDismissableLayer` composable (existing)
- `CategoryDetailModal.vue` imports `FullScreenTrouser`, `Tabs`, `Button`, `KeyValueList`, `GoalEditor`
- `FundingModal.vue` imports `FormModal`, `CurrencyField`, `Button`
- `BudgetsPage.vue` imports `CategoryDetailModal`, `FundingModal`, `MoveFundsModal`, `FundGroupModal`
- Types from `web/src/dojo/types.ts`: `Category`, `CategoryGroup`
- State from `web/src/dojo/state/app.ts`: `useAppState()` → `saveCategory`
- Utils from `web/src/dojo/utils/currency.ts`: `formatCurrency`
