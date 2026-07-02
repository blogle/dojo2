# Python Code Hygiene Examples

## Ruff FBT

Ruff FBT is enabled. `just lint-api` catches positional boolean traps.

**Don't** stack booleans until call sites become unreadable.

```python
def update_account(account_id: str, is_hidden: bool, is_closed: bool) -> None:
    ...


update_account(account_id, True, False)
```

**Do** use values that name their own states, or split operations when the combinations are not meaningful.

```python
class AccountVisibility(StrEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


class AccountStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


def update_account(account_id: str, visibility: AccountVisibility, status: AccountStatus) -> None:
    ...


update_account(account_id, AccountVisibility.HIDDEN, AccountStatus.OPEN)
```

**Do** make boolean parameters keyword-only when a boolean remains the right representation.

```python
def list_accounts(*, show_hidden: bool = False) -> list[Account]:
    ...
```

**Don't** make callers decode positional booleans.

```python
list_accounts(True)
```

## Comments

**Do** explain an external constraint or invariant.

```python
# Google Sheets may return helper rows after the visible budget table; keep parsing until
# the configured break symbol rather than stopping at the first blank row.
for row in rows:
    ...
```

**Do** answer what would break if a future maintainer removed the branch.

```python
# Aspire's configuration rows can reference categories deleted from the visible sheet.
# Synthesize a hidden placeholder instead of dropping the transaction so historical
# ledger totals stay reconcilable.
category = categories.get(row.category_id) or synthesize_hidden_category(row)
```

**Don't** narrate the code.

```python
# Loop over rows.
for row in rows:
    ...
```

## Simplicity

**Do** keep a single clear workflow together.

```python
def import_sheet(sheet: SheetDump) -> ImportResult:
    contract = parse_contract(sheet)
    rows = parse_transactions(contract)
    return persist_transactions(rows)
```

**Don't** extract helpers that only rename one line without carrying a concept.

```python
def get_contract(sheet: SheetDump) -> Contract:
    return parse_contract(sheet)
```

**Don't** build a generic strategy system for one real format.

```python
class ImportStrategy(Protocol):
    def can_handle(self, source: SheetSource) -> bool: ...
    def parse(self, source: SheetSource) -> list[Row]: ...


def import_from(source: SheetSource, strategies: list[ImportStrategy]) -> list[Row]:
    for strategy in strategies:
        if strategy.can_handle(source):
            return strategy.parse(source)
    raise UnsupportedSourceError(source)
```

**Do** name the one real thing directly.

```python
def import_from_aspire(source: SheetSource) -> list[Row]:
    ...
```

## Duplicated Decisions

**Do** extract or share a business rule used in two places.

```python
def is_reportable_category(category: Category) -> bool:
    return category.kind == CategoryKind.STANDARD and not category.is_hidden
```

**Don't** hide different domain concepts behind a shared helper just because they both sum amounts.

```python
def total_transaction_amounts(rows: list[TransactionRow]) -> Money:
    return sum_money(row.amount for row in rows)


def total_allocation_amounts(rows: list[AllocationRow]) -> Money:
    return sum_money(row.amount for row in rows)
```

These can stay separate if future transaction and allocation rules are likely to change independently. A shared `total_amounts(rows, skip_zero=False)` helper would add boolean blindness and couple unrelated concepts.

**Don't** extract incidental syntax.

```python
def loop(items: Iterable[Item]) -> Iterator[Item]:
    for item in items:
        yield item
```
