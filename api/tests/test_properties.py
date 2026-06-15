from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from hypothesis import given, settings
from hypothesis import strategies as st

from dojo.constants import STATUS_CLEARED, STATUS_PENDING, SYSTEM_ATB_BUCKET_ID
from dojo.migrations import provision_database
from dojo.service import DojoService
from dojo.sql import render_sql
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
