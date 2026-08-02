from __future__ import annotations

import pytest

from dojo.service import DojoService
from tests.support.clock import MutableClock


def _account(service: DojoService, account_id: str) -> dict[str, object]:
    return next(
        account
        for account in service.list_accounts(show_hidden=True)
        if account["account_id"] == account_id
    )


def _overview_item(service: DojoService, account_id: str) -> dict[str, object]:
    return next(
        item
        for group in service.get_assets_liabilities()["groups"]
        for item in group["items"]
        if item["account_id"] == account_id
    )


def _net_worth_item(service: DojoService, account_id: str) -> dict[str, object]:
    return next(
        item
        for item in service.get_net_worth()["items"]
        if item["account_id"] == account_id and not item["ignored_import_value"]
    )


def test_type_aware_values_are_consistent_across_read_surfaces(
    service: DojoService,
) -> None:
    tracking_asset_id = service.create_account(
        {"name": "Legacy brokerage", "account_class": "TRACKING", "polarity": "ASSET"}
    )["account_id"]
    tracking_liability_id = service.create_account(
        {"name": "Legacy debt", "account_class": "TRACKING", "polarity": "LIABILITY"}
    )["account_id"]
    tangible_id = service.create_account({"name": "Home", "account_class": "TANGIBLE_ASSET"})[
        "account_id"
    ]
    loan_id = service.create_account({"name": "Mortgage", "account_class": "LOAN"})["account_id"]

    service.create_tracking_snapshot(
        tracking_asset_id,
        {"effective_date": "2026-02-01", "amount_minor": 10_000},
    )
    service.create_tracking_snapshot(
        tracking_liability_id,
        {"effective_date": "2026-02-01", "amount_minor": 30_000},
    )
    service.create_tangible_asset_valuation(
        tangible_id,
        {"effective_date": "2026-02-01", "amount_minor": 40_000},
    )
    service.create_loan_snapshot(
        loan_id,
        {
            "effective_date": "2026-02-01",
            "principal_balance_minor": 100_000,
            "accrued_interest_minor": 5_000,
        },
    )

    expected = {
        tracking_asset_id: (10_000, 10_000, "snapshot"),
        tracking_liability_id: (30_000, -30_000, "snapshot"),
        tangible_id: (40_000, 40_000, "manual_valuation"),
        loan_id: (105_000, -105_000, "loan_statement"),
    }
    for account_id, (display_value, net_worth_value, source) in expected.items():
        account = _account(service, account_id)
        overview = _overview_item(service, account_id)
        net_worth = _net_worth_item(service, account_id)

        assert account["current_value_minor"] == display_value
        assert account["net_worth_contribution_minor"] == net_worth_value
        assert account["value_source"] == source
        assert overview["value_minor"] == net_worth_value
        assert overview["source_of_truth"] == source
        assert net_worth["net_worth_minor"] == net_worth_value
        assert net_worth["source"] == source

    assert service.get_assets_liabilities()["net_worth_minor"] == -85_000
    assert service.get_net_worth()["current_net_worth_minor"] == -85_000


def test_future_effective_values_do_not_apply_early(service: DojoService) -> None:
    tracking_id = service.create_account(
        {"name": "Future tracking", "account_class": "TRACKING", "polarity": "ASSET"}
    )["account_id"]
    tangible_id = service.create_account(
        {"name": "Future tangible", "account_class": "TANGIBLE_ASSET"}
    )["account_id"]
    loan_id = service.create_account({"name": "Future loan", "account_class": "LOAN"})["account_id"]

    service.create_tracking_snapshot(
        tracking_id,
        {"effective_date": "2026-02-01", "amount_minor": 10_000},
    )
    service.create_tracking_snapshot(
        tracking_id,
        {"effective_date": "2026-03-01", "amount_minor": 20_000},
    )
    service.create_tangible_asset_valuation(
        tangible_id,
        {"effective_date": "2026-03-01", "amount_minor": 30_000},
    )
    service.create_loan_snapshot(
        loan_id,
        {"effective_date": "2026-03-01", "principal_balance_minor": 40_000},
    )

    assert _account(service, tracking_id)["current_value_minor"] == 10_000
    assert _account(service, tangible_id)["current_value_minor"] is None
    assert _account(service, loan_id)["current_value_minor"] is None
    assert _overview_item(service, tangible_id)["attention_status"] == "MISSING_VALUE"
    assert _overview_item(service, loan_id)["attention_status"] == "MISSING_VALUE"


def test_same_date_tracking_and_tangible_values_are_scd_corrections(
    service: DojoService, clock: MutableClock
) -> None:
    tracking_id = service.create_account(
        {"name": "Corrected tracking", "account_class": "TRACKING", "polarity": "ASSET"}
    )["account_id"]
    tangible_id = service.create_account(
        {"name": "Corrected tangible", "account_class": "TANGIBLE_ASSET"}
    )["account_id"]

    first_tracking = service.create_tracking_snapshot(
        tracking_id,
        {"effective_date": "2026-02-01", "amount_minor": 10_000},
    )
    first_tangible = service.create_tangible_asset_valuation(
        tangible_id,
        {"effective_date": "2026-02-01", "amount_minor": 20_000},
    )
    clock.advance(seconds=1)
    corrected_tracking = service.create_tracking_snapshot(
        tracking_id,
        {"effective_date": "2026-02-01", "amount_minor": 11_000},
    )
    corrected_tangible = service.create_tangible_asset_valuation(
        tangible_id,
        {"effective_date": "2026-02-01", "amount_minor": 21_000},
    )

    assert corrected_tracking == first_tracking
    assert corrected_tangible == first_tangible
    assert [row["amount_minor"] for row in service.list_tracking_snapshots(tracking_id)] == [11_000]
    assert [row["amount_minor"] for row in service.list_tangible_asset_valuations(tangible_id)] == [
        21_000
    ]
    tracking_history = service.db.fetch_all(
        "SELECT amount_minor FROM net_worth_valuations WHERE valuation_id = ? ORDER BY valid_from",
        (first_tracking["valuation_id"],),
    )
    tangible_history = service.db.fetch_all(
        "SELECT amount_minor FROM tangible_asset_valuations WHERE valuation_id = ? ORDER BY valid_from",
        (first_tangible["valuation_id"],),
    )
    assert [row["amount_minor"] for row in tracking_history] == [10_000, 11_000]
    assert [row["amount_minor"] for row in tangible_history] == [20_000, 21_000]


def test_snapshot_writes_reject_the_wrong_account_class(service: DojoService) -> None:
    budget_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]

    with pytest.raises(ValueError, match="Account must be TRACKING"):
        service.create_tracking_snapshot(
            budget_id,
            {"effective_date": "2026-02-01", "amount_minor": 10_000},
        )
    with pytest.raises(ValueError, match="Account must be TANGIBLE_ASSET"):
        service.create_tangible_asset_valuation(
            budget_id,
            {"effective_date": "2026-02-01", "amount_minor": 10_000},
        )


def test_investment_statement_value_applies_post_statement_transfers_provisionally(
    service: DojoService,
) -> None:
    checking_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    investment_id = service.create_account({"name": "Brokerage", "account_class": "INVESTMENT"})[
        "account_id"
    ]
    service.reconcile_investment_statement(
        investment_id,
        {
            "effective_date": "2026-02-01",
            "cash_balance_minor": 5_000,
            "holdings": [
                {
                    "ticker": "VTI",
                    "quantity_micros": 2_500_000,
                    "price_minor": 10_000,
                    "average_basis_minor": 8_000,
                }
            ],
        },
    )

    before = _account(service, investment_id)
    assert before["current_value_minor"] == 30_000
    assert before["provisional_value_minor"] == 0
    assert before["reconciliation_status"] == "CURRENT"
    assert service.get_net_worth()["current_net_worth_minor"] == 30_000

    service.create_transfer(
        from_account_id=checking_id,
        to_account_id=investment_id,
        amount_minor=10_000,
        transfer_date=service.clock.today(),
        memo="Investment contribution",
        status="CLEARED",
    )

    provisional = _account(service, investment_id)
    assert provisional["current_value_minor"] == 40_000
    assert provisional["provisional_value_minor"] == 10_000
    assert provisional["reconciliation_status"] == "PROVISIONAL"
    assert service.get_net_worth()["current_net_worth_minor"] == 30_000

    service.reconcile_investment_statement(
        investment_id,
        {
            "effective_date": service.clock.today(),
            "cash_balance_minor": 15_000,
            "holdings": [
                {
                    "ticker": "VTI",
                    "quantity_micros": 2_500_000,
                    "price_minor": 10_000,
                }
            ],
        },
    )
    reconciled = _account(service, investment_id)
    assert reconciled["current_value_minor"] == 40_000
    assert reconciled["provisional_value_minor"] == 0
    assert reconciled["reconciliation_status"] == "CURRENT"
    assert service.get_net_worth()["current_net_worth_minor"] == 30_000


def test_investment_contribution_funds_linked_category_and_withdrawal_returns_atb(
    service: DojoService,
) -> None:
    checking_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    investment_id = service.create_account({"name": "Brokerage", "account_class": "INVESTMENT"})[
        "account_id"
    ]
    group_id = service.create_category_group(
        {"name": "Investing", "sort_order": 1, "is_hidden": False}
    )["group_id"]
    category_id = service.create_category(
        {
            "group_id": group_id,
            "name": "Investment Contributions",
            "category_kind": "STANDARD",
            "sort_order": 1,
        }
    )["category_id"]
    service.set_account_budget_link(
        investment_id,
        {
            "category_id": category_id,
            "link_behavior": "INVESTMENT_CONTRIBUTION",
            "effective_date": "2026-02-01",
        },
    )
    service.reconcile_investment_statement(
        investment_id,
        {"effective_date": "2026-02-01", "cash_balance_minor": 0, "holdings": []},
    )

    contribution = service.create_investment_transfer(
        investment_id,
        {
            "direction": "CONTRIBUTION",
            "budget_account_id": checking_id,
            "date": service.clock.today(),
            "amount_minor": 10_000,
            "status": "CLEARED",
            "memo": "Contribution",
            "fund_shortfall": True,
        },
    )
    assert contribution["funded_shortfall_minor"] == 10_000
    assert service.compute_category_available(category_id) == 0
    assert service.compute_available_to_budget() == -10_000
    assert service.get_net_worth()["current_net_worth_minor"] == 0

    service.create_investment_transfer(
        investment_id,
        {
            "direction": "WITHDRAWAL",
            "budget_account_id": checking_id,
            "date": service.clock.today(),
            "amount_minor": 4_000,
            "status": "CLEARED",
            "memo": "Withdrawal",
        },
    )
    assert service.compute_available_to_budget() == -6_000
    assert _account(service, investment_id)["current_value_minor"] == 6_000
    assert service.get_net_worth()["current_net_worth_minor"] == 0


def test_loan_reconciliation_derives_aggregate_principal_and_unknown_remainder(
    service: DojoService,
) -> None:
    checking_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    loan_id = service.create_account({"name": "Mortgage", "account_class": "LOAN"})["account_id"]
    group_id = service.create_category_group(
        {"name": "Bills", "sort_order": 1, "is_hidden": False}
    )["group_id"]
    category_id = service.create_category(
        {
            "group_id": group_id,
            "name": "Mortgage payment",
            "category_kind": "STANDARD",
            "sort_order": 1,
        }
    )["category_id"]
    service.create_loan_snapshot(
        loan_id,
        {
            "effective_date": "2026-01-01",
            "principal_balance_minor": 20_000_000,
            "escrow_balance_minor": 1_000_000,
            "unapplied_credit_minor": 0,
        },
    )
    service.create_loan_payment(
        loan_id,
        {
            "date": "2026-02-01",
            "budget_account_id": checking_id,
            "amount_minor": 500_000,
            "category_id": category_id,
            "status": "CLEARED",
            "memo": "Mortgage payment",
        },
    )
    service.create_loan_payment(
        loan_id,
        {
            "date": "2026-02-10",
            "budget_account_id": checking_id,
            "amount_minor": 100_000,
            "category_id": category_id,
            "status": "PENDING",
            "memo": "Pending mortgage payment",
        },
    )
    service.create_loan_snapshot(
        loan_id,
        {
            "effective_date": "2026-02-15",
            "principal_balance_minor": 19_800_000,
            "accrued_interest_minor": 100_000,
            "escrow_balance_minor": 1_200_000,
            "unapplied_credit_minor": 50_000,
        },
    )

    latest = service.list_loan_snapshots(loan_id)[0]
    assert latest["attributed_payment_minor"] == 500_000
    assert latest["principal_reduction_minor"] == 200_000
    assert latest["unknown_nonprincipal_minor"] == 300_000
    assert len(service.list_loan_payments(loan_id)) == 2
    loan = _account(service, loan_id)
    assert loan["current_value_minor"] == 19_900_000
    assert loan["net_worth_contribution_minor"] == -18_650_000
