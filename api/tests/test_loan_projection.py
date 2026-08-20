from datetime import date

from dojo.loan_projection import LoanProjectionTerms, project_loan


def _terms(**overrides: object) -> LoanProjectionTerms:
    values: dict[str, object] = {
        "principal_minor": 120_000,
        "principal_as_of": date(2026, 1, 1),
        "annual_rate_minor": 0,
        "rate_type": "FIXED",
        "scheduled_payment_minor": 10_000,
        "payment_frequency": "MONTHLY",
        "next_payment_date": date(2026, 2, 1),
        "maturity_date": None,
        "remaining_term_months": 12,
        "recurring_extra_principal_minor": 0,
    }
    values.update(overrides)
    return LoanProjectionTerms(**values)  # type: ignore[arg-type]


def test_zero_rate_projection_pays_off_on_schedule() -> None:
    projection = project_loan(_terms(), as_of=date(2026, 1, 15))

    assert projection["available"] is True
    assert projection["projected_payoff_date"] == "2027-01-01"
    assert projection["projected_total_interest_minor"] == 0
    assert len(projection["rows"]) == 12  # type: ignore[arg-type]


def test_projection_estimates_interest_and_extra_principal() -> None:
    projection = project_loan(
        _terms(
            principal_minor=100_000,
            annual_rate_minor=1_200,
            rate_type="VARIABLE",
            recurring_extra_principal_minor=1_000,
            remaining_term_months=24,
        ),
        as_of=date(2026, 2, 1),
    )

    first = projection["rows"][0]  # type: ignore[index]
    assert projection["rate_assumption"] == "Current variable rate held constant"
    assert projection["estimated_accrued_interest_minor"] == 1_019
    assert first["interest_minor"] == 1_000
    assert first["principal_minor"] == 10_000
    assert first["payment_minor"] == 11_000


def test_projection_reports_missing_or_non_amortizing_terms() -> None:
    missing = project_loan(_terms(next_payment_date=None), as_of=date(2026, 1, 1))
    assert missing == {"available": False, "missing": ["next payment date"], "rows": []}

    non_amortizing = project_loan(
        _terms(annual_rate_minor=12_000, scheduled_payment_minor=10_000),
        as_of=date(2026, 1, 1),
    )
    assert non_amortizing["available"] is False
    assert non_amortizing["reason"] == "Scheduled payment does not exceed estimated interest"

    stale = project_loan(_terms(), as_of=date(2026, 2, 2))
    assert stale["available"] is False
    assert stale["reason"] == "Next payment date is before the projection date"
