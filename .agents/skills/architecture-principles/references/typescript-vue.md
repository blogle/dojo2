# TypeScript and Vue Architecture Examples

## Parse, Don't Validate

**Don't** keep validity in a side-channel boolean that must stay synchronized with raw state.

```ts
const rawAmount = ref('')
const isAmountValid = ref(false)

watch(rawAmount, (value) => {
  isAmountValid.value = !Number.isNaN(parseFloat(value)) && parseFloat(value) !== 0
})

function submit() {
  if (isAmountValid.value) save({ amount: parseFloat(rawAmount.value) })
}
```

**Do** parse raw state into a result whose shape carries the invariant.

```ts
type ParsedAmount = { ok: true; value: number } | { ok: false; error: string }

function parseAmount(raw: string): ParsedAmount {
  const value = parseFloat(raw)
  if (Number.isNaN(value) || value === 0) return { ok: false, error: 'Enter a nonzero amount' }
  return { ok: true, value }
}

const parsed = computed(() => parseAmount(rawAmount.value))

function submit() {
  if (parsed.value.ok) save({ amount: parsed.value.value })
}
```

**Do** convert API responses into domain-shaped values before core UI logic depends on them.

```ts
type TransactionStatus = 'cleared' | 'pending'

type Transaction = {
  id: TransactionId
  status: TransactionStatus
  amountMinor: number
}
```

**Don't** pass `Record<string, unknown>` or raw JSON through components and composables that expect domain data.

```ts
function statusLabel(transaction: Record<string, unknown>) {
  if (transaction.status === 'cleared') return 'Cleared'
  return 'Pending'
}
```

## Discriminated Unions

**Do** model variant state explicitly.

```ts
type LoadState<T> =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'loaded'; value: T }
  | { kind: 'failed'; message: string }
```

**Don't** coordinate multiple booleans or nullable fields that can contradict each other.

```ts
type LoadState<T> = {
  isLoading: boolean
  value: T | null
  error: string | null
}
```

## Boolean Props and Options

Boolean props are acceptable when their meaning is obvious at the call site, such as `disabled` or `open`. Prefer explicit variants when a boolean selects behavior.

**Do** use explicit modes for behavior choices.

```ts
type Density = 'compact' | 'comfortable'
```

**Don't** make callers remember what `true` means.

```vue
<CategoryTable :dense="true" :interactive="false" />
```

## String-Programming

**Do** use unions or lookup tables for known commands.

```ts
type BudgetCommand = 'fund-category' | 'move-funds' | 'return-to-atb'

const handlers: Record<BudgetCommand, () => Promise<void>> = {
  'fund-category': fundCategory,
  'move-funds': moveFunds,
  'return-to-atb': returnToAtb,
}
```

**Don't** spread magic strings through event handlers and branch chains.

```ts
if (action === 'fund') await fundCategory()
if (action === 'move') await moveFunds()
```

## Component Boundaries

Keep components responsible for rendering and interaction. Move domain transformations to composables or pure functions when they can be tested without mounting the component.

**Don't** fetch, compute, and format inside component setup.

```vue
<script setup lang="ts">
const budget = ref<Budget | null>(null)

onMounted(async () => {
  const response = await fetch(`/api/budget/${currentMonth.value}`)
  const data = await response.json()
  const totalAvailable = data.categories.reduce(
    (sum: number, category: any) => sum + category.budgeted + category.activity,
    0,
  )
  budget.value = { ...data, display: `$${(totalAvailable / 100).toFixed(2)}` }
})
</script>
```

**Do** let the shell fetch and plain functions derive values.

```ts
export function computeTotalAvailable(categories: CategorySnapshot[]): number {
  return categories.reduce((sum, category) => sum + category.budgeted + category.activity, 0)
}

export function useBudget(month: Ref<string>) {
  const budget = ref<Budget | null>(null)
  watchEffect(async () => {
    const data = await fetchBudget(month.value)
    budget.value = { ...data, totalAvailable: computeTotalAvailable(data.categories) }
  })
  return { budget }
}
```

**Don't** let pure-looking helpers depend on time.

```ts
export function isStale(transaction: Transaction): boolean {
  return Date.now() - transaction.createdAt > 30 * 24 * 60 * 60 * 1000
}
```

**Do** pass `now` from the shell.

```ts
export function isStale(transaction: Transaction, now: number): boolean {
  return now - transaction.createdAt > 30 * 24 * 60 * 60 * 1000
}
```
