from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class AccountValue:
    current_value_minor: int | None
    net_worth_minor: int
    source_of_truth: str
    effective_date: date | None
    change_minor: int | None
    reconciliation_status: str
    provisional_minor: int = 0
    liability_minor: int = 0
    restricted_asset_minor: int = 0
    unapplied_credit_minor: int = 0


def asset_value(
    amount_minor: int | None,
    *,
    source_of_truth: str,
    effective_date: date | None,
    previous_amount_minor: int | None,
) -> AccountValue:
    current = abs(amount_minor) if amount_minor is not None else None
    previous = abs(previous_amount_minor) if previous_amount_minor is not None else None
    return AccountValue(
        current_value_minor=current,
        net_worth_minor=current or 0,
        source_of_truth=source_of_truth,
        effective_date=effective_date,
        change_minor=_change(current, previous),
        reconciliation_status="NOT_RECONCILED",
    )


def liability_value(
    amount_minor: int | None,
    *,
    source_of_truth: str,
    effective_date: date | None,
    previous_amount_minor: int | None,
) -> AccountValue:
    current = abs(amount_minor) if amount_minor is not None else None
    previous = abs(previous_amount_minor) if previous_amount_minor is not None else None
    return AccountValue(
        current_value_minor=current,
        net_worth_minor=-(current or 0),
        source_of_truth=source_of_truth,
        effective_date=effective_date,
        change_minor=_change(current, previous),
        reconciliation_status="NOT_RECONCILED",
    )


def ledger_value(current_minor: int, previous_minor: int | None) -> AccountValue:
    return AccountValue(
        current_value_minor=current_minor,
        net_worth_minor=current_minor,
        source_of_truth="ledger",
        effective_date=None,
        change_minor=_change(current_minor, previous_minor),
        reconciliation_status="NOT_RECONCILED",
    )


def unavailable_value(source_of_truth: str) -> AccountValue:
    return AccountValue(
        current_value_minor=None,
        net_worth_minor=0,
        source_of_truth=source_of_truth,
        effective_date=None,
        change_minor=None,
        reconciliation_status="NOT_RECONCILED",
    )


def _change(current_minor: int | None, previous_minor: int | None) -> int | None:
    if current_minor is None or previous_minor is None:
        return None
    return current_minor - previous_minor
