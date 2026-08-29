from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from uuid import uuid4

from hypothesis import given, settings
from hypothesis import strategies as st

from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    ACCOUNT_CLASS_INVESTMENT,
    ACCOUNT_CLASS_LOAN,
    BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
    BUDGET_ACCOUNT_TYPE_DEPOSIT,
    DERIVATION_METHOD_CC_SPEND_AND_TRANSFER,
    DERIVATION_METHOD_TRANSFER_IN_ONLY,
    LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
    LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
    LINK_BEHAVIOR_LOAN_PAYMENT,
    MAX_TS,
    STATUS_CLEARED,
    STATUS_PENDING,
    SYSTEM_ATB_BUCKET_ID,
)
from dojo.migrations import provision_database
from dojo.operations import (
    create_transaction_operation,
    link_transaction_operation,
    relink_transaction_operation,
    unlink_transaction_operation,
)
from dojo.scd import insert_version
from dojo.service import DojoService
from dojo.sql import load_sql, render_sql
from tests.support.clock import MutableClock, default_test_clock
from tests.support.scd_invariants import (
    assert_history_preserved_after_edit,
    assert_history_preserved_after_void,
    assert_no_overlapping_versions,
    assert_single_current_version,
)


@contextmanager
def imported_service_context() -> Iterator[tuple[DojoService, MutableClock]]:
    with TemporaryDirectory(prefix="dojo-property-") as temp_dir:
        clock = default_test_clock()
        duckdb_path = Path(temp_dir) / "property.duckdb"
        provision_database(str(duckdb_path))
        service = DojoService(str(duckdb_path), clock=clock)
        result = service.import_sheet_data(source="fixture://default", source_kind="fixture")
        assert result["ok"] is True
        try:
            yield service, clock
        finally:
            service.close()


def total_budget_value(service: DojoService, month: str) -> int:
    categories = service.list_categories(month=month, show_hidden=True)
    return service.compute_available_to_budget() + sum(
        item["available_minor"] for item in categories
    )


def first_standard_category(service: DojoService) -> dict[str, object]:
    return next(
        category
        for category in service.list_categories(month="2026-02", show_hidden=True)
        if category["category_kind"] == "STANDARD"
    )


def first_two_budget_accounts(service: DojoService) -> tuple[dict[str, object], dict[str, object]]:
    accounts = [
        account
        for account in service.list_accounts(show_hidden=True)
        if account["account_class"] == "BUDGET"
    ]
    return accounts[0], accounts[1]


def financial_read_snapshot(service: DojoService) -> dict[str, object]:
    transaction_rows = [
        {
            key: value
            for key, value in row.items()
            if key
            not in {
                "operation_id",
                "operation_kind",
                "transfer_counterparty_account_id",
                "transfer_counterparty_account_name",
            }
        }
        for row in service.list_transactions(limit=10_000, show_hidden=True)["items"]
    ]
    return {
        "accounts": service.list_accounts(show_hidden=True),
        "available_to_budget_minor": service.compute_available_to_budget(),
        "categories": service.list_categories(month="2026-02", show_hidden=True),
        "category_activity": service.list_category_activity(),
        "net_worth": service.get_net_worth(),
        "transactions": transaction_rows,
    }


@settings(max_examples=20, deadline=None)
@given(amounts=st.lists(st.integers(min_value=1, max_value=5_000), min_size=1, max_size=5))
def test_allocations_preserve_total_budget_value(amounts: list[int]) -> None:
    with imported_service_context() as (imported_service, _clock):
        category = first_standard_category(imported_service)
        category_bucket_id = str(category["bucket_id"])
        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        baseline = total_budget_value(imported_service, "2026-02")

        for amount in amounts:
            available = imported_service.compute_available_to_budget()
            move_amount = min(amount, max(0, available))
            if move_amount == 0:
                continue
            imported_service.create_allocation(
                from_bucket_id=atb_bucket_id,
                to_bucket_id=category_bucket_id,
                amount_minor=move_amount,
                memo="fund",
                allocation_date=date(2026, 2, 15),
            )
            assert total_budget_value(imported_service, "2026-02") == baseline
            imported_service.create_allocation(
                from_bucket_id=category_bucket_id,
                to_bucket_id=atb_bucket_id,
                amount_minor=move_amount,
                memo="return",
                allocation_date=date(2026, 2, 15),
            )
            assert total_budget_value(imported_service, "2026-02") == baseline


@settings(max_examples=15, deadline=None)
@given(
    amount_minor=st.integers(min_value=-5_000, max_value=-1),
    initial_status=st.sampled_from([STATUS_PENDING, STATUS_CLEARED]),
)
def test_status_changes_do_not_change_actual_account_balance(
    amount_minor: int, initial_status: str
) -> None:
    with imported_service_context() as (imported_service, clock):
        account, _ = first_two_budget_accounts(imported_service)
        category = first_standard_category(imported_service)
        before = next(
            row
            for row in imported_service.list_accounts(show_hidden=True)
            if row["account_id"] == account["account_id"]
        )

        created = imported_service.create_transaction(
            {
                "date": date(2026, 2, 15),
                "account_id": str(account["account_id"]),
                "amount_minor": amount_minor,
                "category_id": str(category["category_id"]),
                "system_category": None,
                "status": initial_status,
                "memo": "status-property",
            }
        )
        tx = next(
            row
            for row in imported_service.list_transactions(limit=200, show_hidden=True)["items"]
            if row["transaction_id"] == created["transaction_id"]
        )
        clock.advance(seconds=1)
        imported_service.update_transaction(
            str(created["transaction_id"]),
            {
                "date": date(2026, 2, 15),
                "account_id": str(account["account_id"]),
                "amount_minor": amount_minor,
                "category_id": str(category["category_id"]),
                "system_category": None,
                "status": STATUS_CLEARED if initial_status == STATUS_PENDING else STATUS_PENDING,
                "memo": "status-property",
            },
        )
        after = next(
            row
            for row in imported_service.list_accounts(show_hidden=True)
            if row["account_id"] == account["account_id"]
        )
        assert after["actual_balance_minor"] == before["actual_balance_minor"] + amount_minor
        assert tx["amount_minor"] == amount_minor


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_transfers_preserve_current_net_worth(amount_minor: int) -> None:
    with imported_service_context() as (imported_service, _clock):
        source, destination = first_two_budget_accounts(imported_service)
        before = imported_service.get_net_worth()["current_net_worth_minor"]
        result = imported_service.create_transfer(
            from_account_id=str(source["account_id"]),
            to_account_id=str(destination["account_id"]),
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="transfer-property",
            status=STATUS_CLEARED,
        )
        after = imported_service.get_net_worth()["current_net_worth_minor"]
        assert after == before

        rows = imported_service.db.fetch_all(
            render_sql(
                "templates/select_columns_where_ordered",
                columns="transaction_id, amount_minor, valid_from",
                table="current_transactions",
                predicate="transaction_id IN (?, ?)",
                order_by="transaction_id",
            ),
            (result["source_transaction_id"], result["destination_transaction_id"]),
        )
        assert sorted(row["amount_minor"] for row in rows) == [-amount_minor, amount_minor]
        assert len({row["valid_from"] for row in rows}) == 1


@settings(max_examples=15, deadline=None)
@given(
    original_amount=st.integers(min_value=-5_000, max_value=-1),
    updated_amount=st.integers(min_value=-5_000, max_value=-1),
    original_status=st.sampled_from([STATUS_PENDING, STATUS_CLEARED]),
    updated_status=st.sampled_from([STATUS_PENDING, STATUS_CLEARED]),
)
def test_transaction_edits_and_voids_preserve_scd_history(
    original_amount: int,
    updated_amount: int,
    original_status: str,
    updated_status: str,
) -> None:
    with imported_service_context() as (imported_service, clock):
        account, _ = first_two_budget_accounts(imported_service)
        category = first_standard_category(imported_service)
        created = imported_service.create_transaction(
            {
                "date": date(2026, 2, 15),
                "account_id": str(account["account_id"]),
                "amount_minor": original_amount,
                "category_id": str(category["category_id"]),
                "system_category": None,
                "status": original_status,
                "memo": "history-property",
            }
        )
        transaction_id = str(created["transaction_id"])
        original_row = imported_service.db.fetch_one(
            render_sql(
                "templates/select_columns_where",
                columns="valid_from, amount_minor, status",
                table="current_transactions",
                predicate="transaction_id = ?",
            ),
            (transaction_id,),
        )
        assert original_row is not None

        clock.advance(seconds=1)
        imported_service.update_transaction(
            transaction_id,
            {
                "date": date(2026, 2, 15),
                "account_id": str(account["account_id"]),
                "amount_minor": updated_amount,
                "category_id": str(category["category_id"]),
                "system_category": None,
                "status": updated_status,
                "memo": "history-property-updated",
            },
        )
        assert_history_preserved_after_edit(
            imported_service.db,
            "transactions",
            "transaction_id",
            transaction_id,
            before_timestamp=original_row["valid_from"],
            expected_before={"amount_minor": original_amount, "status": original_status},
            expected_current={"amount_minor": updated_amount, "status": updated_status},
        )
        assert_no_overlapping_versions(
            imported_service.db, "transactions", "transaction_id", transaction_id
        )
        assert_single_current_version(
            imported_service.db, "transactions", "transaction_id", transaction_id
        )

        clock.advance(seconds=1)
        imported_service.delete_transaction(transaction_id)
        assert_history_preserved_after_void(
            imported_service.db,
            "transactions",
            "transaction_id",
            transaction_id,
            before_timestamp=original_row["valid_from"],
            expected_before={"amount_minor": original_amount, "status": original_status},
        )


# ---------------------------------------------------------------------------
# Account-category link behavior property tests
# ---------------------------------------------------------------------------


def _first_budget_account(service: DojoService) -> dict[str, object]:
    return next(
        account
        for account in service.list_accounts(show_hidden=True)
        if account["account_class"] == ACCOUNT_CLASS_BUDGET
    )


def _budget_accounts(service: DojoService) -> list[dict[str, object]]:
    return [
        account
        for account in service.list_accounts(show_hidden=True)
        if account["account_class"] == ACCOUNT_CLASS_BUDGET
    ]


def _standard_categories(service: DojoService) -> list[dict[str, object]]:
    return [
        category
        for category in service.list_categories(month="2026-02", show_hidden=True)
        if category["category_kind"] == "STANDARD"
    ]


def _total_budget_value(service: DojoService, month: str) -> int:
    categories = service.list_categories(month=month, show_hidden=True)
    return service.compute_available_to_budget() + sum(
        item["available_minor"] for item in categories
    )


def _category_available(service: DojoService, category_id: str, month: str) -> int:
    categories = service.list_categories(month=month, show_hidden=True)
    cat = next(c for c in categories if c["category_id"] == category_id)
    return cat["available_minor"]


def _create_linked_account_and_category(
    service: DojoService,
    *,
    account_class: str,
    account_name: str,
    category_name: str,
    link_behavior: str,
    budget_account_type: str | None = None,
    polarity: str | None = None,
) -> tuple[str, str]:
    account = service.create_account(
        {
            "name": account_name,
            "account_class": account_class,
            "budget_account_type": budget_account_type,
            "polarity": polarity,
        }
    )
    account_id = account["account_id"]
    category = service.create_category(
        {
            "name": category_name,
            "group_id": str(SYSTEM_ATB_BUCKET_ID),
            "category_kind": "STANDARD",
            "sort_order": 9990,
        }
    )
    category_id = category["category_id"]
    with service.db.transaction() as connection:
        insert_version(
            connection,
            "account_budget_links",
            {
                "account_id": account_id,
                "category_id": category_id,
                "link_behavior": link_behavior,
                "effective_date": date(2026, 2, 1),
                "valid_from": "2026-02-01T00:00:00+00:00",
                "valid_to": MAX_TS,
                "created_at": "2026-02-01T00:00:00+00:00",
                "created_by_user_id": None,
            },
        )
    return account_id, category_id


def _insert_account_budget_link(
    service: DojoService,
    account_id: str,
    category_id: str,
    link_behavior: str,
    effective_date: date = date(2026, 2, 1),
    derivation_method: str | None = None,
) -> None:
    if derivation_method is None:
        if link_behavior == LINK_BEHAVIOR_CREDIT_CARD_PAYMENT:
            derivation_method = DERIVATION_METHOD_CC_SPEND_AND_TRANSFER
        else:
            derivation_method = DERIVATION_METHOD_TRANSFER_IN_ONLY
    with service.db.transaction() as connection:
        connection.execute(
            load_sql("queries/close_account_budget_links_by_account_behavior"),
            ("2026-02-01T00:00:00+00:00", account_id, link_behavior),
        )
        insert_version(
            connection,
            "account_budget_links",
            {
                "account_id": account_id,
                "category_id": category_id,
                "link_behavior": link_behavior,
                "derivation_method": derivation_method,
                "effective_date": effective_date,
                "valid_from": "2026-02-01T00:00:00+00:00",
                "valid_to": MAX_TS,
                "created_at": "2026-02-01T00:00:00+00:00",
                "created_by_user_id": None,
            },
        )


def _count_account_budget_links(service: DojoService, account_id: str) -> int:
    rows = service.db.fetch_all(
        render_sql(
            "templates/select_columns_where",
            columns="row_id",
            table="current_account_budget_links",
            predicate="account_id = ?",
        ),
        (account_id,),
    )
    return len(rows)


# --- Credit card payment link behavior ---


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_credit_card_payment_link_reduces_category_available_on_spend(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        cc_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        account_id = str(cc_account["account_id"])
        category_id = str(category["category_id"])

        _insert_account_budget_link(
            service, account_id, category_id, LINK_BEHAVIOR_CREDIT_CARD_PAYMENT
        )

        # Fund the category
        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor * 2,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Spend on the linked credit card account
        service.create_transaction(
            {
                "date": date(2026, 2, 15),
                "account_id": account_id,
                "amount_minor": -amount_minor,
                "category_id": category_id,
                "system_category": None,
                "status": STATUS_CLEARED,
                "memo": "cc-spend",
            }
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline - amount_minor


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_credit_card_payment_transfer_to_card_does_not_reduce_category(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        accounts = _budget_accounts(service)
        deposit_account = next(
            a for a in accounts if a["budget_account_type"] == BUDGET_ACCOUNT_TYPE_DEPOSIT
        )
        cc_account = next(
            a for a in accounts if a["budget_account_type"] == BUDGET_ACCOUNT_TYPE_CREDIT_CARD
        )
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        deposit_id = str(deposit_account["account_id"])
        cc_id = str(cc_account["account_id"])
        category_id = str(category["category_id"])

        _insert_account_budget_link(service, cc_id, category_id, LINK_BEHAVIOR_CREDIT_CARD_PAYMENT)

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Transfer to the credit card (payment) — should not reduce category
        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=cc_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="cc-payment",
            status=STATUS_CLEARED,
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline


@settings(max_examples=10, deadline=None)
@given(
    amount=st.integers(min_value=1, max_value=5_000),
    effective_date=st.dates(min_value=date(2026, 2, 1), max_value=date(2026, 2, 28)),
)
def test_credit_card_payment_link_is_prospective(amount: int, effective_date: date) -> None:
    with imported_service_context() as (service, clock):
        cc_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        account_id = str(cc_account["account_id"])
        category_id = str(category["category_id"])

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount,
            memo="fund",
            allocation_date=date(2026, 1, 15),
        )

        # Spend before the link is created
        service.create_transaction(
            {
                "date": date(2026, 1, 20),
                "account_id": account_id,
                "amount_minor": -amount,
                "category_id": category_id,
                "system_category": None,
                "status": STATUS_CLEARED,
                "memo": "pre-link-spend",
            }
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Create the link with a future effective date
        _insert_account_budget_link(
            service,
            account_id,
            category_id,
            LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
            effective_date=effective_date,
        )

        # Historical spend should not be reinterpreted
        assert _category_available(service, category_id, "2026-02") == baseline


# --- Investment contribution link behavior ---


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_investment_contribution_link_reduces_category_on_transfer_in(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        deposit_id = str(deposit_account["account_id"])
        category_id = str(category["category_id"])

        # Create investment account with linked contribution category
        inv_account = service.create_account(
            {
                "name": "Test Brokerage",
                "account_class": ACCOUNT_CLASS_INVESTMENT,
            }
        )
        inv_id = inv_account["account_id"]

        _insert_account_budget_link(
            service,
            inv_id,
            category_id,
            LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
        )

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor * 2,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Transfer from budget to investment — linked behavior reduces category
        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=inv_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="contribution",
            status=STATUS_CLEARED,
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline - amount_minor


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_investment_contribution_transfer_out_does_not_reduce_category(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        deposit_id = str(deposit_account["account_id"])
        category_id = str(category["category_id"])

        inv_account = service.create_account(
            {
                "name": "Test Brokerage",
                "account_class": ACCOUNT_CLASS_INVESTMENT,
            }
        )
        inv_id = inv_account["account_id"]

        _insert_account_budget_link(
            service,
            inv_id,
            category_id,
            LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
        )

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Transfer from investment back to budget (withdrawal)
        service.create_transfer(
            from_account_id=inv_id,
            to_account_id=deposit_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="withdrawal",
            status=STATUS_CLEARED,
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_investment_contribution_transfers_between_budget_accounts_preserve_net_worth(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        deposit_id = str(deposit_account["account_id"])

        accounts = _budget_accounts(service)
        other_deposit = next(
            a
            for a in accounts
            if a["account_id"] != deposit_account["account_id"]
            and a["budget_account_type"] == BUDGET_ACCOUNT_TYPE_DEPOSIT
        )
        other_id = str(other_deposit["account_id"])

        before_nw = service.get_net_worth()["current_net_worth_minor"]

        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=other_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="budget-transfer",
            status=STATUS_CLEARED,
        )

        after_nw = service.get_net_worth()["current_net_worth_minor"]
        assert after_nw == before_nw


# --- Loan payment link behavior ---


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_loan_payment_link_reduces_category_on_transfer_in(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        deposit_id = str(deposit_account["account_id"])
        category_id = str(category["category_id"])

        loan_account = service.create_account(
            {
                "name": "Test Mortgage",
                "account_class": ACCOUNT_CLASS_LOAN,
                "original_amount_minor": 200_000_00,
                "rate_minor": 4_50,
            }
        )
        loan_id = loan_account["account_id"]

        _insert_account_budget_link(
            service,
            loan_id,
            category_id,
            LINK_BEHAVIOR_LOAN_PAYMENT,
        )

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor * 2,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Transfer from budget to loan — linked behavior reduces category
        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=loan_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="loan-payment",
            status=STATUS_CLEARED,
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline - amount_minor


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_loan_payment_transfer_out_does_not_reduce_category(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        standard_cats = _standard_categories(service)
        category = standard_cats[0]
        deposit_id = str(deposit_account["account_id"])
        category_id = str(category["category_id"])

        loan_account = service.create_account(
            {
                "name": "Test Mortgage",
                "account_class": ACCOUNT_CLASS_LOAN,
                "original_amount_minor": 200_000_00,
                "rate_minor": 4_50,
            }
        )
        loan_id = loan_account["account_id"]

        _insert_account_budget_link(
            service,
            loan_id,
            category_id,
            LINK_BEHAVIOR_LOAN_PAYMENT,
        )

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        service.create_allocation(
            from_bucket_id=atb_bucket_id,
            to_bucket_id=category_id,
            amount_minor=amount_minor,
            memo="fund",
            allocation_date=date(2026, 2, 1),
        )

        baseline = _category_available(service, category_id, "2026-02")

        # Transfer from loan back to budget (disbursement / refund)
        service.create_transfer(
            from_account_id=loan_id,
            to_account_id=deposit_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="loan-disbursement",
            status=STATUS_CLEARED,
        )

        after = _category_available(service, category_id, "2026-02")
        assert after == baseline


@settings(max_examples=15, deadline=None)
@given(amount_minor=st.integers(min_value=1, max_value=10_000))
def test_loan_payment_transfers_between_budget_accounts_preserve_net_worth(
    amount_minor: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        deposit_id = str(deposit_account["account_id"])

        accounts = _budget_accounts(service)
        other_deposit = next(
            a
            for a in accounts
            if a["account_id"] != deposit_account["account_id"]
            and a["budget_account_type"] == BUDGET_ACCOUNT_TYPE_DEPOSIT
        )
        other_id = str(other_deposit["account_id"])

        before_nw = service.get_net_worth()["current_net_worth_minor"]

        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=other_id,
            amount_minor=amount_minor,
            transfer_date=date(2026, 2, 15),
            memo="budget-transfer",
            status=STATUS_CLEARED,
        )

        after_nw = service.get_net_worth()["current_net_worth_minor"]
        assert after_nw == before_nw


# --- Link uniqueness constraint ---


@settings(max_examples=5, deadline=None)
@given(
    behavior=st.sampled_from(
        [
            LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
            LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
            LINK_BEHAVIOR_LOAN_PAYMENT,
        ]
    )
)
def test_one_account_cannot_have_two_active_links_for_same_behavior(
    behavior: str,
) -> None:
    with imported_service_context() as (service, _clock):
        account = service.create_account(
            {
                "name": "Dual-Link Test Account",
                "account_class": ACCOUNT_CLASS_BUDGET,
                "budget_account_type": BUDGET_ACCOUNT_TYPE_DEPOSIT,
            }
        )
        account_id = account["account_id"]

        cat1 = service.create_category(
            {
                "name": "Category One",
                "group_id": str(SYSTEM_ATB_BUCKET_ID),
                "category_kind": "STANDARD",
                "sort_order": 9991,
            }
        )
        cat2 = service.create_category(
            {
                "name": "Category Two",
                "group_id": str(SYSTEM_ATB_BUCKET_ID),
                "category_kind": "STANDARD",
                "sort_order": 9992,
            }
        )

        for category_id in [cat1["category_id"], cat2["category_id"]]:
            _insert_account_budget_link(
                service,
                account_id,
                category_id,
                behavior,
            )

        active_links = _count_account_budget_links(service, account_id)
        # Only one should be active at a time — the second should supersede the first
        assert active_links == 1


# --- Cross-behavior link independence ---


@settings(max_examples=5, deadline=None)
@given(
    amount=st.integers(min_value=1, max_value=5_000),
)
def test_different_link_behaviors_on_same_account_are_independent(
    amount: int,
) -> None:
    with imported_service_context() as (service, _clock):
        deposit_account = _first_budget_account(service)
        deposit_id = str(deposit_account["account_id"])

        standard_cats = _standard_categories(service)
        cat1 = standard_cats[0]
        cat2 = standard_cats[1] if len(standard_cats) > 1 else standard_cats[0]
        cat1_id = str(cat1["category_id"])
        cat2_id = str(cat2["category_id"])

        inv_account = service.create_account(
            {"name": "Brokerage", "account_class": ACCOUNT_CLASS_INVESTMENT}
        )
        loan_account = service.create_account(
            {
                "name": "Mortgage",
                "account_class": ACCOUNT_CLASS_LOAN,
                "original_amount_minor": 200_000_00,
                "rate_minor": 4_50,
            }
        )

        for link_acct, link_cat, behavior in [
            (inv_account["account_id"], cat1_id, LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION),
            (loan_account["account_id"], cat2_id, LINK_BEHAVIOR_LOAN_PAYMENT),
        ]:
            _insert_account_budget_link(
                service,
                link_acct,
                link_cat,
                behavior,
            )

        atb_bucket_id = str(SYSTEM_ATB_BUCKET_ID)
        for cat_id in [cat1_id, cat2_id]:
            service.create_allocation(
                from_bucket_id=atb_bucket_id,
                to_bucket_id=cat_id,
                amount_minor=amount * 2,
                memo="fund",
                allocation_date=date(2026, 2, 1),
            )

        cat1_before = _category_available(service, cat1_id, "2026-02")
        cat2_before = _category_available(service, cat2_id, "2026-02")

        # Contribution to investment affects only cat1
        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=inv_account["account_id"],
            amount_minor=amount,
            transfer_date=date(2026, 2, 10),
            memo="invest",
            status=STATUS_CLEARED,
        )

        assert _category_available(service, cat1_id, "2026-02") == cat1_before - amount
        assert _category_available(service, cat2_id, "2026-02") == cat2_before

        # Payment to loan affects only cat2
        service.create_transfer(
            from_account_id=deposit_id,
            to_account_id=loan_account["account_id"],
            amount_minor=amount,
            transfer_date=date(2026, 2, 15),
            memo="loan-pay",
            status=STATUS_CLEARED,
        )

        assert _category_available(service, cat1_id, "2026-02") == cat1_before - amount
        assert _category_available(service, cat2_id, "2026-02") == cat2_before - amount


def test_operation_provenance_changes_do_not_change_financial_reads() -> None:
    with imported_service_context() as (service, clock):
        transaction_rows = service.db.fetch_all(
            "SELECT transaction_id FROM current_transactions ORDER BY entry_order LIMIT 2"
        )
        assert len(transaction_rows) == 2
        source_transaction_id = str(transaction_rows[0]["transaction_id"])
        destination_transaction_id = str(transaction_rows[1]["transaction_id"])
        first_operation_id = str(uuid4())
        second_operation_id = str(uuid4())
        before = financial_read_snapshot(service)

        with service.db.transaction() as connection:
            create_transaction_operation(
                connection,
                operation_id=first_operation_id,
                operation_kind="TRANSFER",
                origin="USER",
                client_operation_id=str(uuid4()),
                request_fingerprint="first",
                created_at=clock.now(),
            )
            link_transaction_operation(
                connection,
                operation_id=first_operation_id,
                transaction_id=source_transaction_id,
                leg_role="SOURCE",
                now=clock.now(),
            )
            link_transaction_operation(
                connection,
                operation_id=first_operation_id,
                transaction_id=destination_transaction_id,
                leg_role="DESTINATION",
                now=clock.now(),
            )
        assert financial_read_snapshot(service) == before

        clock.advance(seconds=1)
        with service.db.transaction() as connection:
            create_transaction_operation(
                connection,
                operation_id=second_operation_id,
                operation_kind="TRANSFER",
                origin="USER",
                client_operation_id=str(uuid4()),
                request_fingerprint="second",
                created_at=clock.now(),
            )
            relink_transaction_operation(
                connection,
                operation_id=second_operation_id,
                transaction_id=source_transaction_id,
                leg_role="SOURCE",
                now=clock.now(),
            )
            unlink_transaction_operation(
                connection,
                operation_id=first_operation_id,
                transaction_id=destination_transaction_id,
                now=clock.now(),
            )
        assert financial_read_snapshot(service) == before
