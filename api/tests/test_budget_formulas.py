from __future__ import annotations

from datetime import date

from dojo.fixture_data import DEFAULT_FIXTURE
from dojo.service import DojoService


def test_fixture_import_succeeds(imported_service: DojoService) -> None:
    assert imported_service.get_app_status()["ready"] is True


def test_fixture_snapshot_matches_expected(imported_service: DojoService) -> None:
    snapshot = imported_service.snapshot_for_validation(months=["2026-01", "2026-02"])
    expected = DEFAULT_FIXTURE["expected"]
    assert snapshot["account_count"] == expected["account_count"]
    assert snapshot["category_group_count"] == expected["category_group_count"]
    assert snapshot["category_count"] == expected["category_count"]
    assert snapshot["net_worth_valuation_rows"] == expected["net_worth_valuation_rows"]
    assert snapshot["account_balances"] == expected["account_balances"]
    assert snapshot["atb_available_minor"] == expected["atb_available_minor"]
    assert snapshot["category_available"] == expected["category_available"]
    assert snapshot["month_activity"] == expected["month_activity"]
    assert snapshot["month_budgeted"] == expected["month_budgeted"]
    assert snapshot["starting_available"] == expected["starting_available"]
    assert snapshot["native_net_worth_minor"] == expected["native_net_worth_minor"]


def test_credit_card_payment_category_behavior(imported_service: DojoService) -> None:
    categories = imported_service.list_categories(month="2026-02", show_hidden=True)
    payment_category = next(
        category for category in categories if category["name"] == "Reserve Card Payment"
    )
    assert payment_category["available_minor"] == 15000


def test_available_to_budget_ignores_liability_starting_balance_outflows(
    imported_service: DojoService,
) -> None:
    assert imported_service.compute_available_to_budget() == 424000


def test_hidden_categories_and_accounts_are_preserved(imported_service: DojoService) -> None:
    hidden_account = next(
        account
        for account in imported_service.list_accounts(show_hidden=True)
        if account["name"] == "Wallet"
    )
    hidden_category = next(
        category
        for category in imported_service.list_categories(month="2026-02", show_hidden=True)
        if category["name"] == "Secret Stash"
    )
    assert hidden_account["is_hidden"] is True
    assert hidden_account["actual_balance_minor"] == 15000
    assert hidden_category["is_hidden"] is True
    assert hidden_category["available_minor"] == 6000


def test_net_worth_rollup_ignores_budget_account_import_values(
    imported_service: DojoService,
) -> None:
    net_worth = imported_service.get_net_worth()
    ignored_budget_entries = [
        item for item in net_worth["items"] if item.get("ignored_import_value")
    ]
    assert any(item["account_name"] == "Checking" for item in ignored_budget_entries)
    assert net_worth["current_net_worth_minor"] == 49469000


def test_status_toggle_changes_pending_and_cleared_without_changing_actual(
    imported_service: DojoService,
) -> None:
    transaction = next(
        row
        for row in imported_service.list_transactions(limit=100, show_hidden=True)
        if row["memo"] == "Hidden category spend"
    )
    before = next(
        account
        for account in imported_service.list_accounts(show_hidden=True)
        if account["name"] == "Checking"
    )
    imported_service.update_transaction(
        transaction["transaction_id"],
        {
            "date": transaction["date"],
            "account_id": transaction["account_id"],
            "amount_minor": transaction["amount_minor"],
            "category_id": transaction["category_id"],
            "system_category": None,
            "status": "CLEARED",
            "memo": transaction["memo"],
        },
    )
    after = next(
        account
        for account in imported_service.list_accounts(show_hidden=True)
        if account["name"] == "Checking"
    )
    assert before["actual_balance_minor"] == after["actual_balance_minor"]
    assert before["pending_balance_minor"] + 4000 == after["pending_balance_minor"]
    assert before["cleared_balance_minor"] - 4000 == after["cleared_balance_minor"]


def test_transaction_edit_and_delete_preserve_history(imported_service: DojoService) -> None:
    account_id = imported_service.list_accounts(show_hidden=True)[0]["account_id"]
    created = imported_service.create_transaction(
        {
            "date": date(2026, 3, 1),
            "account_id": account_id,
            "amount_minor": -1234,
            "category_id": None,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "PENDING",
            "memo": "history-test",
        }
    )
    transaction_id = created["transaction_id"]
    original = imported_service.db.fetch_one(
        "SELECT valid_from FROM current_transactions WHERE transaction_id = ?", (transaction_id,)
    )
    assert original is not None
    original_valid_from = original["valid_from"]

    imported_service.update_transaction(
        transaction_id,
        {
            "date": date(2026, 3, 1),
            "account_id": account_id,
            "amount_minor": -999,
            "category_id": None,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "CLEARED",
            "memo": "history-test-updated",
        },
    )

    as_of_before_edit = imported_service.db.fetch_one(
        "SELECT amount_minor, status FROM transactions WHERE transaction_id = ? AND valid_from <= ? AND ? < valid_to",
        (transaction_id, original_valid_from, original_valid_from),
    )
    current = imported_service.db.fetch_one(
        "SELECT amount_minor, status FROM current_transactions WHERE transaction_id = ?",
        (transaction_id,),
    )
    assert as_of_before_edit == {"amount_minor": -1234, "status": "PENDING"}
    assert current == {"amount_minor": -999, "status": "CLEARED"}

    imported_service.delete_transaction(transaction_id)
    assert (
        imported_service.db.fetch_one(
            "SELECT transaction_id FROM current_transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        is None
    )
