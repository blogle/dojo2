"""Pure transfer effects at the budget boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class TransferBoundaryFact:
    transaction_id: str
    account_class: str
    system_category: str | None
    amount_minor: int
    effective_date: date
    status: str


def compute_transfer_boundary_adjustment(facts: list[TransferBoundaryFact], *, as_of: date) -> int:
    """Calculate ATB's supported transfer-boundary contribution without provenance."""
    adjustment = 0
    for fact in facts:
        if fact.effective_date > as_of or fact.system_category != "TX_ACCOUNT_TRANSFER":
            continue
        if fact.account_class == "BUDGET":
            adjustment += fact.amount_minor
        elif fact.account_class == "INVESTMENT" and fact.amount_minor > 0:
            adjustment += fact.amount_minor
    return adjustment
