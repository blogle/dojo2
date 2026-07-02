# Shared Architecture Examples

## Duplicated Decisions

The repo already has a durable example in `DECISIONS.md`: `get_budget` once called `list_categories`, then called `list_category_groups`, which recomputed categories internally. Passing `precomputed_categories` removed duplicated aggregation decisions and real runtime cost.

**Do** remove duplicated decisions that can drift or waste work.

```text
Compute category aggregation once, then pass the result to consumers that need the same decision.
```

**Don't** chase coincidental similarity.

```text
Two functions both loop over rows, but they answer different domain questions. That is not necessarily duplication.
```

## Responsibility

**Do** split when code has multiple reasons to change.

```text
One boundary parses HTTP input. One core function computes the budget. One shell function persists or returns the result.
```

**Don't** split only because a function crossed an arbitrary line count.

```text
A single clear workflow can stay together if extracting helpers would hide the sequence and create names with no independent meaning.
```

**Don't** collapse batching, computation, and formatting into one loop to solve performance.

```text
Fetch category rows, fetch transaction rows for each category, compute activity, handle credit-card adjustments, and format response dictionaries in one pass.
```

**Do** precompute shared data once per concern, then join it in a core calculation.

```text
Fetch transaction sums by category. Fetch credit-card adjustments. Compute category activity from plain maps. Format the response at the boundary.
```

## Compatibility

**Do** add compatibility paths for persisted data, shipped behavior, external consumers, or explicit requirements.

**Don't** add speculative fallback branches because a future caller might need them.
