from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from pydantic import ValidationError

from dojo.api.models import AccountPayload
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
        if item["account_id"] == account_id and item.get("component_kind") is None
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


def test_future_effective_values_are_rejected(service: DojoService) -> None:
    tracking_id = service.create_account(
        {"name": "Future tracking", "account_class": "TRACKING", "polarity": "ASSET"}
    )["account_id"]
    tangible_id = service.create_account(
        {"name": "Future tangible", "account_class": "TANGIBLE_ASSET"}
    )["account_id"]
    loan_id = service.create_account({"name": "Future loan", "account_class": "LOAN"})["account_id"]
    investment_id = service.create_account(
        {"name": "Future investment", "account_class": "INVESTMENT"}
    )["account_id"]

    service.create_tracking_snapshot(
        tracking_id,
        {"effective_date": "2026-02-01", "amount_minor": 10_000},
    )

    assert _account(service, tracking_id)["current_value_minor"] == 10_000
    future_date = "2026-03-01"
    future_writes = [
        (
            "tracking snapshot",
            lambda: service.create_tracking_snapshot(
                tracking_id, {"effective_date": future_date, "amount_minor": 20_000}
            ),
        ),
        (
            "tangible valuation",
            lambda: service.create_tangible_asset_valuation(
                tangible_id, {"effective_date": future_date, "amount_minor": 30_000}
            ),
        ),
        (
            "loan statement",
            lambda: service.create_loan_snapshot(
                loan_id, {"effective_date": future_date, "principal_balance_minor": 40_000}
            ),
        ),
        (
            "investment position",
            lambda: service.create_investment_position(
                investment_id,
                {"effective_date": future_date, "ticker": "VTI", "quantity_micros": 1_000_000},
            ),
        ),
        (
            "investment cash",
            lambda: service.create_investment_cash_snapshot(
                investment_id, {"effective_date": future_date, "cash_balance_minor": 10_000}
            ),
        ),
        (
            "investment price",
            lambda: service.create_investment_price_snapshot(
                {"effective_date": future_date, "ticker": "VTI", "price_minor": 25_000}
            ),
        ),
        (
            "investment statement",
            lambda: service.reconcile_investment_statement(
                investment_id,
                {"effective_date": future_date, "cash_balance_minor": 10_000, "holdings": []},
            ),
        ),
        (
            "opening tangible valuation",
            lambda: service.create_account(
                {
                    "name": "Future opening value",
                    "account_class": "TANGIBLE_ASSET",
                    "opening_valuation_minor": 50_000,
                    "opening_valuation_date": future_date,
                }
            ),
        ),
    ]
    for label, future_write in future_writes:
        try:
            future_write()
        except ValueError as error:
            assert "cannot be in the future" in str(error)
        else:
            pytest.fail(f"{label} accepted a future effective date")


def test_loan_creation_requires_and_records_current_principal(service: DojoService) -> None:
    with pytest.raises(ValidationError, match="Loan creation requires"):
        AccountPayload(name="Mortgage", account_class="LOAN")

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
    loan_id = service.create_account(
        {
            "name": "Mortgage",
            "account_class": "LOAN",
            "current_principal_minor": 24_000_000,
            "current_principal_as_of": "2026-02-01",
            "loan_payment_category_id": category_id,
            "rate_minor": 600,
            "rate_type": "FIXED",
            "scheduled_principal_interest_minor": 200_000,
            "payment_frequency": "MONTHLY",
            "next_payment_date": "2026-03-01",
            "remaining_term_months": 180,
        }
    )["account_id"]

    snapshot = service.list_loan_snapshots(loan_id)[0]
    assert snapshot["principal_balance_minor"] == 24_000_000
    assert snapshot["effective_date"].isoformat() == "2026-02-01"
    assert service.list_account_budget_links(loan_id)[0]["category_id"] == category_id
    projection = service.get_loan_projection(loan_id)
    assert projection["available"] is True
    assert projection["rows"]


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


def test_tracking_cutover_is_atomic_idempotent_and_activates_on_date(
    service: DojoService, clock: MutableClock
) -> None:
    tracking_id = service.create_account(
        {"name": "Legacy assets", "account_class": "TRACKING", "polarity": "ASSET"}
    )["account_id"]
    service.create_tracking_snapshot(
        tracking_id, {"effective_date": "2026-02-01", "amount_minor": 30_000}
    )
    payload = {
        "operation_id": "5c3d76b6-0b53-49ec-84b7-78532c7ddf04",
        "cutover_date": "2026-03-01",
        "expected_predecessor_value_minor": 30_000,
        "variance_confirmed": False,
        "successors": [
            {
                "account_class": "INVESTMENT",
                "name": "Brokerage",
                "cash_balance_minor": 10_000,
                "holdings": [],
            },
            {
                "account_class": "TANGIBLE_ASSET",
                "name": "Collectible",
                "opening_value_minor": 20_000,
            },
        ],
    }

    start = Barrier(3)

    def apply_cutover() -> dict[str, object]:
        start.wait()
        return service.create_tracking_cutover(tracking_id, payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(apply_cutover) for _ in range(2)]
        start.wait()
        first, repeated = [future.result() for future in futures]

    assert repeated == first
    successor_ids = first["successor_account_ids"]
    assert len(successor_ids) == 2

    before = service.list_accounts(show_hidden=False)
    assert {account["account_id"] for account in before} == {tracking_id}
    assert service.get_net_worth()["current_net_worth_minor"] == 30_000

    clock.advance(days=14)
    after = service.list_accounts(show_hidden=False)
    assert {account["account_id"] for account in after} == set(successor_ids)
    assert service.get_net_worth()["current_net_worth_minor"] == 30_000
    assert service.list_tracking_snapshots(tracking_id)[0]["amount_minor"] == 30_000

    conflicting = payload | {"successors": [payload["successors"][0] | {"name": "Changed name"}]}
    with pytest.raises(ValueError, match="different content"):
        service.create_tracking_cutover(tracking_id, conflicting)


def test_tracking_liability_cutover_preserves_signed_net_worth(service: DojoService) -> None:
    group_id = service.create_category_group(
        {"name": "Bills", "sort_order": 1, "is_hidden": False}
    )["group_id"]
    category_id = service.create_category(
        {
            "group_id": group_id,
            "name": "Loan payment",
            "category_kind": "STANDARD",
            "sort_order": 1,
        }
    )["category_id"]
    tracking_id = service.create_account(
        {"name": "Legacy loan", "account_class": "TRACKING", "polarity": "LIABILITY"}
    )["account_id"]
    service.create_tracking_snapshot(
        tracking_id, {"effective_date": "2026-02-01", "amount_minor": 10_000}
    )

    result = service.create_tracking_cutover(
        tracking_id,
        {
            "operation_id": "fa1f2b8c-353a-409b-814a-d10cbac0f035",
            "cutover_date": service.clock.today(),
            "expected_predecessor_value_minor": 10_000,
            "variance_confirmed": False,
            "successors": [
                {
                    "account_class": "LOAN",
                    "name": "Loan",
                    "payment_category_id": category_id,
                    "principal_balance_minor": 11_000,
                    "escrow_balance_minor": 1_000,
                }
            ],
        },
    )

    assert result["successor_total_minor"] == -10_000
    assert result["variance_minor"] == 0
    assert service.get_net_worth()["current_net_worth_minor"] == -10_000
    overview = service.get_assets_liabilities()
    assert overview["liabilities_minor"] == -11_000
    assert overview["assets_minor"] == 1_000


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
    category = next(
        item
        for item in service.list_categories(month="2026-02", show_hidden=False)
        if item["category_id"] == category_id
    )
    assert category["month_activity_minor"] == -10_000
    derived_activity = [
        item
        for item in service.list_category_activity()
        if item["category_id"] == category_id and item["is_derived"]
    ]
    assert len(derived_activity) == 1
    assert derived_activity[0]["amount_minor"] == -10_000
    assert derived_activity[0]["account_name"] == "Brokerage"
    investment_activity = service.list_transactions(
        limit=10,
        show_hidden=False,
        account_id=investment_id,
    )["items"]
    assert investment_activity[0]["transfer_counterparty_account_id"] == checking_id
    assert investment_activity[0]["transfer_counterparty_account_name"] == "Checking"

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
    assert len([item for item in service.list_category_activity() if item["is_derived"]]) == 1


def test_same_day_investment_transfer_uses_statement_version_order(
    service: DojoService, clock: MutableClock
) -> None:
    group_id = service.create_category_group(
        {"name": "Investing", "sort_order": 1, "is_hidden": False}
    )["group_id"]
    category_id = service.create_category(
        {
            "group_id": group_id,
            "name": "Contributions",
            "category_kind": "STANDARD",
            "sort_order": 1,
        }
    )["category_id"]
    checking_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    investment_id = service.create_account(
        {
            "name": "Brokerage",
            "account_class": "INVESTMENT",
            "investment_contribution_category_id": category_id,
        }
    )["account_id"]
    service.reconcile_investment_statement(
        investment_id,
        {"effective_date": clock.today(), "cash_balance_minor": 0, "holdings": []},
    )

    service.create_investment_transfer(
        investment_id,
        {
            "direction": "CONTRIBUTION",
            "budget_account_id": checking_id,
            "date": clock.today(),
            "amount_minor": 10_000,
            "status": "CLEARED",
            "memo": "Same-day contribution",
            "fund_shortfall": True,
        },
    )
    provisional = _account(service, investment_id)
    assert provisional["current_value_minor"] == 10_000
    assert provisional["provisional_value_minor"] == 10_000

    service.reconcile_investment_statement(
        investment_id,
        {"effective_date": clock.today(), "cash_balance_minor": 10_000, "holdings": []},
    )
    reconciled = _account(service, investment_id)
    assert reconciled["current_value_minor"] == 10_000
    assert reconciled["provisional_value_minor"] == 0


def test_investment_link_changes_preserve_prior_derived_category_activity(
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
    category_ids = [
        service.create_category(
            {
                "group_id": group_id,
                "name": name,
                "category_kind": "STANDARD",
                "sort_order": index,
            }
        )["category_id"]
        for index, name in enumerate(("Old contributions", "New contributions"), start=1)
    ]
    service.set_account_budget_link(
        investment_id,
        {
            "category_id": category_ids[0],
            "link_behavior": "INVESTMENT_CONTRIBUTION",
            "effective_date": "2026-02-01",
        },
    )
    service.reconcile_investment_statement(
        investment_id,
        {"effective_date": "2026-02-01", "cash_balance_minor": 0, "holdings": []},
    )
    service.set_account_budget_link(
        investment_id,
        {
            "category_id": category_ids[1],
            "link_behavior": "INVESTMENT_CONTRIBUTION",
            "effective_date": "2026-02-15",
        },
    )
    service.create_investment_transfer(
        investment_id,
        {
            "direction": "CONTRIBUTION",
            "budget_account_id": checking_id,
            "date": "2026-02-10",
            "amount_minor": 10_000,
            "status": "CLEARED",
            "memo": "Old link",
        },
    )
    service.create_investment_transfer(
        investment_id,
        {
            "direction": "CONTRIBUTION",
            "budget_account_id": checking_id,
            "date": "2026-02-15",
            "amount_minor": 20_000,
            "status": "CLEARED",
            "memo": "New link",
        },
    )

    categories = {
        item["category_id"]: item
        for item in service.list_categories(month="2026-02", show_hidden=False)
    }
    assert categories[category_ids[0]]["month_activity_minor"] == -10_000
    assert categories[category_ids[1]]["month_activity_minor"] == -20_000
    derived = [item for item in service.list_category_activity() if item["is_derived"]]
    assert {(item["category_id"], item["amount_minor"]) for item in derived} == {
        (category_ids[0], -10_000),
        (category_ids[1], -20_000),
    }


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
    service.set_account_budget_link(
        loan_id,
        {
            "category_id": category_id,
            "link_behavior": "LOAN_PAYMENT",
            "effective_date": "2026-01-01",
        },
    )
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
            "ytd_principal_paid_minor": 200_000,
            "ytd_interest_paid_minor": 300_000,
        },
    )

    latest = service.list_loan_snapshots(loan_id)[0]
    assert latest["attributed_payment_minor"] == 500_000
    assert latest["principal_reduction_minor"] == 200_000
    assert latest["unknown_nonprincipal_minor"] == 300_000
    assert latest["ytd_principal_paid_minor"] == 200_000
    assert latest["ytd_interest_paid_minor"] == 300_000
    assert len(service.list_loan_payments(loan_id)) == 2
    loan = _account(service, loan_id)
    assert loan["current_value_minor"] == 19_900_000
    assert loan["net_worth_contribution_minor"] == -18_650_000
    overview = service.get_assets_liabilities()
    loan_item = next(
        item
        for group in overview["groups"]
        for item in group["items"]
        if item["account_id"] == loan_id and item.get("component_kind") is None
    )
    restricted_items = [
        item
        for group in overview["groups"]
        for item in group["items"]
        if item["account_id"] == loan_id and item.get("component_kind") is not None
    ]
    assert loan_item["value_minor"] == -19_900_000
    assert {(item["component_kind"], item["value_minor"]) for item in restricted_items} == {
        ("ESCROW", 1_200_000),
        ("UNAPPLIED_CREDIT", 50_000),
    }
    net_worth_items = [
        item
        for item in service.get_net_worth()["items"]
        if item["account_id"] == loan_id and not item["ignored_import_value"]
    ]
    assert {(item["component_kind"], item["net_worth_minor"]) for item in net_worth_items} == {
        ("LOAN_LIABILITY", -19_900_000),
        ("ESCROW", 1_200_000),
        ("UNAPPLIED_CREDIT", 50_000),
    }
