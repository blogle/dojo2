from datetime import date

from dojo.transfer_boundary import TransferBoundaryFact, compute_transfer_boundary_adjustment


def fact(
    transaction_id: str,
    account_class: str,
    amount_minor: int,
    effective_date: date = date(2026, 1, 1),
    *,
    has_effective_budget_link: bool = False,
) -> TransferBoundaryFact:
    return TransferBoundaryFact(
        transaction_id=transaction_id,
        account_class=account_class,
        system_category="TX_ACCOUNT_TRANSFER",
        amount_minor=amount_minor,
        effective_date=effective_date,
        status="PENDING",
        has_effective_budget_link=has_effective_budget_link,
    )


def test_raw_account_transfer_never_changes_atb_even_when_unmatched() -> None:
    assert (
        compute_transfer_boundary_adjustment([fact("out", "BUDGET", -100)], as_of=date(2026, 1, 1))
        == 0
    )
    assert (
        compute_transfer_boundary_adjustment([fact("in", "BUDGET", 100)], as_of=date(2026, 1, 1))
        == 0
    )


def test_budget_to_budget_transfer_has_zero_boundary_effect_even_with_missing_leg() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("out", "BUDGET", -100), fact("in", "BUDGET", 100)],
            as_of=date(2026, 1, 1),
        )
        == 0
    )


def test_investment_contribution_has_no_atb_effect() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("contribution", "INVESTMENT", 100, has_effective_budget_link=True)],
            as_of=date(2026, 1, 1),
        )
        == 0
    )


def test_linked_investment_withdrawal_returns_positive_budget_amount() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [
                fact(
                    "out",
                    "INVESTMENT",
                    -100,
                    has_effective_budget_link=True,
                )
            ],
            as_of=date(2026, 1, 1),
        )
        == 100
    )


def test_unlinked_investment_withdrawal_does_not_change_atb() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("out", "INVESTMENT", -100)], as_of=date(2026, 1, 1)
        )
        == 0
    )


def test_boundary_excludes_future_facts() -> None:
    assert (
        compute_transfer_boundary_adjustment(
            [fact("future", "BUDGET", 100, date(2026, 1, 2))],
            as_of=date(2026, 1, 1),
        )
        == 0
    )
