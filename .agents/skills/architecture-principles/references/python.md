# Python Architecture Examples

Examples are illustrative; adapt names and imports to the code under edit.

## Functional Core

**Don't** let core logic reach out for its own inputs.

```python
def compute_month_activity(category_id: str, month: str) -> Decimal:
    conn = duckdb.connect(DB_PATH)
    rows = conn.execute(
        "SELECT amount FROM transactions WHERE category_id = ?",
        [category_id],
    ).fetchall()
    return sum(row[0] for row in rows)
```

**Do** let the shell fetch and the core decide.

```python
def compute_month_activity(transactions: list[TransactionRow], month: str) -> Decimal:
    return sum(transaction.amount for transaction in transactions if transaction.month == month)


rows = fetch_transactions_for_month(conn, month)
activity = compute_month_activity(rows, month)
```

**Don't** hide time inside pure-looking helpers.

```python
def is_transaction_stale(transaction: TransactionRow) -> bool:
    return (datetime.now() - transaction.created_at).days > 30
```

**Do** pass time in from the shell.

```python
def is_transaction_stale(transaction: TransactionRow, now: datetime) -> bool:
    return (now - transaction.created_at).days > 30


is_transaction_stale(transaction, clock.now())
```

## Parse, Don't Validate

**Don't** validate with a boolean and then re-parse later.

```python
def is_valid_amount(raw: str) -> bool:
    try:
        Decimal(raw)
        return True
    except InvalidOperation:
        return False


if is_valid_amount(raw):
    amount = Decimal(raw)
```

**Do** parse once and return the parsed value or explicit failure.

```python
@dataclass(frozen=True, slots=True)
class AmountParseError:
    raw: str


def parse_amount(raw: str) -> Decimal | AmountParseError:
    try:
        return Decimal(raw)
    except InvalidOperation:
        return AmountParseError(raw)


match parse_amount(raw):
    case Decimal() as amount:
        save_amount(amount)
    case AmountParseError(raw=bad):
        report_invalid_amount(bad)
```

## Boolean Blindness

Ruff FBT is enabled for the API. Prefer keyword-only boolean parameters when a boolean is still the right representation.

**Do** name boolean arguments at the call site.

```python
budget = service.get_budget(month, show_hidden=True)
```

**Do** make route/query booleans keyword-only.

```python
def budget(request: Request, *, month: str | None = None, show_hidden: bool = False) -> dict[str, Any]:
    ...
```

**Don't** add positional boolean traps.

```python
def get_budget(month: str, show_hidden: bool = False) -> Budget:
    ...

get_budget("2026-07", True)
```

When multiple booleans appear together, prefer values that name the valid states.

**Don't** make every combination type-check.

```python
def import_sheet(source: str, dry_run: bool, skip_validation: bool, force: bool) -> None:
    ...


import_sheet("fixture", True, False, True)
```

**Do** collapse the valid combinations into a mode.

```python
class ImportMode(StrEnum):
    DRY_RUN = "dry_run"
    VALIDATE = "validate"
    FORCE = "force"


def import_sheet(source: str, mode: ImportMode) -> None:
    ...


import_sheet("fixture", ImportMode.DRY_RUN)
```

## Structural Control Flow

**Do** use `match` when branching on known variants.

```python
match row.kind:
    case TransactionRowKind.REAL_TRANSACTION:
        return parse_transaction(row)
    case TransactionRowKind.BLANK_ROW | TransactionRowKind.IGNORED_HELPER_ROW:
        return None
    case TransactionRowKind.BREAK_ROW:
        return BreakMarker()
```

**Don't** replace simple guard clauses with pattern matching.

```python
if amount_minor <= 0:
    raise ValueError("amount must be positive")
```

## String-Programming

**Do** parse strings into enums or typed IDs before core logic.

```python
status = TransactionStatus(raw_status)
```

**Don't** dispatch on raw strings throughout core logic.

```python
if payload["status"] == "cleared":
    ...
elif payload["status"] == "pending":
    ...
```

## Single Responsibility

**Don't** fetch, compute, and format in one function.

```python
def get_category_summary(conn, category_id: str) -> dict[str, str]:
    rows = conn.execute("SELECT amount FROM transactions WHERE category_id = ?", [category_id]).fetchall()
    total = sum(row.amount for row in rows)
    return {"display": f"${total / 100:,.2f}"}
```

**Do** split by reason to change.

```python
def fetch_category_transactions(conn, category_id: str) -> list[TransactionRow]: ...
def compute_month_total(transactions: list[TransactionRow], month: str) -> Decimal: ...
def format_currency(amount: Decimal) -> str: ...
```
