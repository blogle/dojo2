from datetime import date

from dojo.transfer_boundary import TransferBoundaryFact, compute_transfer_boundary_adjustment


def fact(
    transaction_id: str,
    account_class: str,
    amount_minor: int,
    effective_date: date = date(2026, 1, 1),
) -> TransferBoundaryFact:
    return TransferBoundaryFact(
        transaction_id=transaction_id,
        account_class=account_class,
        system_category="TX_ACCOUNT_TRANSFER",
        amount_minor=amount_minor,
        effective_date=effective_date,
        status="PENDING",
    )


def test_complete_budget_transfer_has_zero_boundary_effect() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("out", "BUDGET", -100), fact("in", "BUDGET", 100)],
            as_of=date(2026, 1, 1),
        )
        == 0
    )


def test_investment_contribution_has_zero_boundary_effect() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("out", "BUDGET", -100), fact("in", "INVESTMENT", 100)],
            as_of=date(2026, 1, 1),
        )
        == 0
    )


def test_investment_withdrawal_returns_positive_budget_amount() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("out", "INVESTMENT", -100), fact("in", "BUDGET", 100)],
            as_of=date(2026, 1, 1),
        )
        == 100
    )


def test_boundary_excludes_future_facts() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("future", "BUDGET", 100, date(2026, 1, 2))],
            as_of=date(2026, 1, 1),
        )
        == 0
    )
