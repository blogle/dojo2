# Shared Code Hygiene Examples

## Semantic Comments

**Do** comment the why.

```text
This branch preserves imported historical rows because deleting them would make
account reconciliation disagree with the source sheet.
```

A useful comment usually answers: why would someone be tempted to delete or change this line, and what would break if they did?

**Don't** comment the what.

```text
This branch checks if the row is historical.
```

## Simplicity

**Do** make the smallest correct change that fits existing structure.

```text
Add a keyword-only parameter to the existing function when the call graph already owns the concept.
```

**Don't** add a framework, registry, strategy object, or config option for one caller.

```text
Create a plugin system for two hard-coded import variants that have no external consumers.
```

## Duplication

**Do** remove repeated decisions.

```text
The same aggregation rule appears in two service methods. Compute it once or share the rule.
```

Do not wait for three occurrences when it is genuinely the same business rule. The rule of three is about incidental similarity, not tolerating known duplicated decisions.

**Don't** deduplicate coincidental shape.

```text
Two components both render a title and a list, but they represent different concepts and are likely to evolve independently.
```

## Structural Control Flow

**Do** prefer explicit structure for variants.

```text
Branch on a tagged state with pattern matching, a discriminated union, or a lookup table.
```

**Don't** make simple logic clever.

```text
Keep early returns and two-way guards when they are the clearest expression.
```
