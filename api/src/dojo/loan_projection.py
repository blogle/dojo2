from __future__ import annotations

from calendar import monthrange
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from math import ceil
from typing import Literal

PaymentFrequency = Literal["MONTHLY", "BIWEEKLY", "WEEKLY"]


@dataclass(frozen=True, slots=True)
class LoanProjectionTerms:
    principal_minor: int
    principal_as_of: date
    annual_rate_minor: int | None
    rate_type: str | None
    scheduled_payment_minor: int | None
    payment_frequency: PaymentFrequency | None
    next_payment_date: date | None
    maturity_date: date | None
    remaining_term_months: int | None
    recurring_extra_principal_minor: int


@dataclass(frozen=True, slots=True)
class LoanProjectionRow:
    payment_number: int
    payment_date: date
    payment_minor: int
    principal_minor: int
    interest_minor: int
    remaining_principal_minor: int


def project_loan(terms: LoanProjectionTerms, *, as_of: date) -> dict[str, object]:
    missing = [
        label
        for label, value in (
            ("interest rate", terms.annual_rate_minor),
            ("scheduled principal-and-interest payment", terms.scheduled_payment_minor),
            ("payment frequency", terms.payment_frequency),
            ("next payment date", terms.next_payment_date),
        )
        if value is None
    ]
    if missing:
        return {"available": False, "missing": missing, "rows": []}

    assert terms.annual_rate_minor is not None
    assert terms.scheduled_payment_minor is not None
    assert terms.payment_frequency is not None
    assert terms.next_payment_date is not None
    if terms.next_payment_date < as_of:
        return {
            "available": False,
            "missing": [],
            "reason": "Next payment date is before the projection date",
            "rows": [],
        }

    periods_per_year = {"MONTHLY": 12, "BIWEEKLY": 26, "WEEKLY": 52}[terms.payment_frequency]
    annual_rate = Decimal(terms.annual_rate_minor) / Decimal(10_000)
    periodic_rate = annual_rate / Decimal(periods_per_year)
    scheduled_total = terms.scheduled_payment_minor + terms.recurring_extra_principal_minor
    period_limit = _period_limit(terms.remaining_term_months, periods_per_year)
    balance = terms.principal_minor
    payment_date = terms.next_payment_date
    total_interest = 0
    rows: list[LoanProjectionRow] = []

    while balance > 0 and len(rows) < period_limit:
        if terms.maturity_date is not None and payment_date > terms.maturity_date:
            break
        interest = _rounded_minor(Decimal(balance) * periodic_rate)
        if scheduled_total <= interest:
            return {
                "available": False,
                "missing": [],
                "reason": "Scheduled payment does not exceed estimated interest",
                "rows": [],
            }
        principal = min(scheduled_total - interest, balance)
        payment = principal + interest
        balance -= principal
        total_interest += interest
        rows.append(
            LoanProjectionRow(
                payment_number=len(rows) + 1,
                payment_date=payment_date,
                payment_minor=payment,
                principal_minor=principal,
                interest_minor=interest,
                remaining_principal_minor=balance,
            )
        )
        payment_date = _next_payment_date(payment_date, terms.payment_frequency)

    elapsed_days = max((as_of - terms.principal_as_of).days, 0)
    accrued = _rounded_minor(
        Decimal(terms.principal_minor) * annual_rate * Decimal(elapsed_days) / Decimal(365)
    )
    rate_assumption = "Current rate held constant"
    if terms.rate_type == "VARIABLE":
        rate_assumption = "Current variable rate held constant"
    elif terms.rate_type == "FIXED":
        rate_assumption = "Current fixed rate"
    return {
        "available": True,
        "missing": [],
        "rate_assumption": rate_assumption,
        "estimated_accrued_interest_minor": accrued,
        "projected_payoff_date": rows[-1].payment_date.isoformat()
        if balance == 0 and rows
        else None,
        "projected_total_interest_minor": total_interest,
        "remaining_principal_at_horizon_minor": balance,
        "rows": [asdict(row) | {"payment_date": row.payment_date.isoformat()} for row in rows],
    }


def _period_limit(remaining_term_months: int | None, periods_per_year: int) -> int:
    if remaining_term_months is None:
        return 1_200
    return min(ceil(remaining_term_months * periods_per_year / 12), 1_200)


def _rounded_minor(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _next_payment_date(current: date, frequency: PaymentFrequency) -> date:
    if frequency == "WEEKLY":
        return current + timedelta(weeks=1)
    if frequency == "BIWEEKLY":
        return current + timedelta(weeks=2)
    month_index = current.month
    year = current.year + month_index // 12
    month = month_index % 12 + 1
    day = min(current.day, monthrange(year, month)[1])
    return date(year, month, day)
