"""Eval fixture: parser shape for test-planning prompt."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Transaction:
    posted_at: date
    amount: Decimal
    account_name: str
    category_name: str


@dataclass(frozen=True, slots=True)
class RowParseError:
    row_number: int
    reason: str


def parse_transaction_row(row_number: int, row: list[str]) -> Transaction | RowParseError:
    if len(row) < 4:
        return RowParseError(row_number, "missing required columns")
    if not row[0] or not row[2]:
        return RowParseError(row_number, "missing required date or account")
    return Transaction(
        posted_at=date.fromisoformat(row[0]),
        amount=Decimal(row[1]),
        account_name=row[2],
        category_name=row[3],
    )
