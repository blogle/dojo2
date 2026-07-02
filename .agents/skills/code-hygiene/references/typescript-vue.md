# TypeScript and Vue Code Hygiene Examples

## Boolean Props

**Don't** make a component consumer cross-reference source to understand adjacent booleans.

```vue
<TransactionRow :is-pending="true" :is-highlighted="false" />
```

**Do** use one named state when the values are variants of the same concept.

```vue
<TransactionRow status="pending" />
```

```ts
type RowStatus = 'pending' | 'reconciled' | 'flagged'
defineProps<{ status: RowStatus }>()
```

Reserve standalone booleans for props whose names disambiguate them in isolation, such as `disabled`, `readonly`, or `open`.

**Do** use booleans whose meaning is obvious at the call site.

```vue
<FormModal :open="isOpen" />
```

**Don't** use booleans to encode unclear behavior choices.

```vue
<BudgetTable :compact="true" :summary="false" />
```

Prefer explicit modes when the prop changes behavior.

```ts
type BudgetTableMode = 'detail' | 'summary'
type Density = 'compact' | 'comfortable'
```

## Comments

**Do** explain why a UI interaction is constrained.

```ts
// Keep focus in the modal until the leave transition completes; otherwise Safari
// drops focus back to the document body and keyboard users lose their place.
```

**Do** tie comments to durable repo decisions when that is the real context.

```ts
// The bootstrap payload intentionally omits budget fields (see DECISIONS.md 2026-06-12).
// Keep the spinner up until refreshBudget() resolves so the UI does not flash stale totals.
loading.value = true
```

**Don't** restate the next line.

```ts
// Set isOpen to false.
isOpen.value = false
```

## Component Hygiene

**Do** move reusable domain transformations out of components.

```ts
export function categoryProgress(category: Category): ProgressState {
  ...
}
```

**Don't** hide business rules inside template-only conditionals when they are reused elsewhere.

```vue
<StateBadge v-if="category.availableMinor < 0 && !category.isHidden" label="Overspent" />
```

## Simplicity

**Don't** build a fully generic config-driven table before a second genuinely configurable table exists.

```ts
interface ColumnConfig<T> {
  key: keyof T
  label: string
  formatter?: (value: unknown) => string
  sortable?: boolean
  width?: string
}

function renderTable<T>(rows: T[], columns: ColumnConfig<T>[]) {
  // ...
}
```

**Do** render the table that exists today. Generalize after the second real case shows what the abstraction needs.

## Tests

Prefer tests around rendered behavior for components and pure function tests for extracted transformations. Avoid tests that assert private helper names or incidental call order.
