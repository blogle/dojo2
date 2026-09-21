from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import duckdb
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from dojo.constants import MAX_TS
from dojo.reconciliation import (
    LocalRecord,
    SourceRecord,
    compare_records,
    resolve_transaction_working_set,
    transaction_digest,
)
from dojo.scd import batch_insert_versions


def test_compare_records_classifies_explicit_identity_and_unmatched_rows() -> None:
    local = LocalRecord(
        transaction_id="local-1",
        valid_from="2026-08-21T00:00:00+00:00",
        account_id="account-1",
        posted_date=date(2026, 8, 20),
        signed_amount_minor=-100,
        status="CLEARED",
        category_id="category-1",
        system_category=None,
        memo="Groceries",
        source_record_id="provider-1",
    )
    exact = SourceRecord("provider-1", date(2026, 8, 20), -100, "CLEARED")
    mismatch = SourceRecord("provider-1", date(2026, 8, 21), -100, "CLEARED")
    result = compare_records(
        [local], [exact, mismatch, SourceRecord("provider-2", date.today(), 20, "PENDING")]
    )
    assert len(result["exact_matches"]) == 1
    assert result["mismatches"][0]["fields"] == ["date"]
    assert result["source_only"] == [{"source_record_id": "provider-2"}]
    assert transaction_digest(local) == transaction_digest(local)


def test_reconciliation_attempt_is_not_canonical_until_successful_certification(service) -> None:
    account_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    transaction = service.create_transaction(
        {
            "date": date(2026, 8, 20),
            "account_id": account_id,
            "amount_minor": 1_000,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "Opening",
        }
    )
    transaction_id = transaction["transaction_id"]
    draft = service.create_reconciliation_draft(
        account_id,
        {
            "source_kind": "BANK_STATEMENT",
            "period_start": date(2026, 8, 1),
            "cutoff": date(2026, 8, 20),
            "source_ending_value_minor": 1_100,
            "source_records": [
                {
                    "source_record_id": "bank-1",
                    "transaction_id": transaction_id,
                    "posted_date": date(2026, 8, 20),
                    "signed_amount_minor": 1_000,
                    "source_status": "CLEARED",
                    "description": "Opening",
                }
            ],
        },
    )
    assert draft["difference_minor"] == 100
    assert service.db.fetch_one("SELECT COUNT(*) AS count FROM reconciliation_commits") == {
        "count": 0
    }

    matching_attempt = service.create_reconciliation_draft(
        account_id,
        {
            "source_kind": "BANK_STATEMENT",
            "period_start": date(2026, 8, 1),
            "cutoff": date(2026, 8, 20),
            "source_ending_value_minor": 1_000,
            "source_records": [
                {
                    "source_record_id": "bank-1",
                    "transaction_id": transaction_id,
                    "posted_date": date(2026, 8, 20),
                    "signed_amount_minor": 1_000,
                    "source_status": "CLEARED",
                }
            ],
        },
    )
    operation_id = str(uuid4())
    with pytest.raises(ValueError, match="matching canonical balance"):
        service.apply_reconciliation(
            draft["reconciliation_id"],
            {"client_operation_id": operation_id},
        )
    assert service.db.fetch_one("SELECT COUNT(*) AS count FROM transactions") == {"count": 1}
    assert service.db.fetch_one("SELECT COUNT(*) AS count FROM reconciliation_commits") == {
        "count": 0
    }
    result = service.apply_reconciliation(
        matching_attempt["reconciliation_id"], {"client_operation_id": operation_id}
    )
    assert result["state"] == "SUCCESSFUL"
    assert (
        service.apply_reconciliation(
            matching_attempt["reconciliation_id"], {"client_operation_id": operation_id}
        )
        == result
    )


def test_shared_commit_history_round_trip_is_immutable_and_supports_void(service) -> None:
    budget_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    tracking_id = service.create_account({"name": "Vehicle", "account_class": "TRACKING"})[
        "account_id"
    ]
    source_as_of = datetime(2026, 8, 31, 17, 0, tzinfo=timezone.utc)
    committed_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    budget_commit = service.create_reconciliation_commit(
        budget_id,
        {
            "reconciliation_id": str(uuid4()),
            "committed_at": committed_at,
            "baseline_digest": "budget-baseline",
            "evidence": {
                "entity_id": budget_id,
                "entity_class": "BUDGET",
                "evidence_kind": "LIVE_BALANCE",
                "source_adapter": "manual",
                "source_as_of": source_as_of,
                "normalized_payload": {"cleared_minor": 1000, "pending_minor": 0},
                "records": [
                    {
                        "source_record_id": "bank-row-1",
                        "posted_date": date(2026, 8, 31),
                        "signed_amount_minor": 1000,
                        "settlement_state": "CLEARED",
                    },
                    {
                        "source_record_id": "bank-row-2",
                        "posted_date": date(2026, 8, 31),
                        "signed_amount_minor": 0,
                        "settlement_state": "PENDING",
                    },
                ],
            },
        },
    )
    tracking_commit = service.create_reconciliation_commit(
        tracking_id,
        {
            "committed_at": committed_at,
            "evidence": {
                "entity_id": tracking_id,
                "entity_class": "TRACKING",
                "evidence_kind": "VALUATION_SNAPSHOT",
                "source_adapter": "manual",
                "source_as_of": source_as_of,
                "normalized_payload": {"value_minor": 20_000},
            },
        },
    )

    stored = service.reconciliation_repository.read_commit(budget_commit["reconciliation_id"])
    assert stored["evidence"]["normalized_payload"] == {"cleared_minor": 1000, "pending_minor": 0}
    assert stored["evidence"]["records"][0]["signed_amount_minor"] == 1000
    assert len(stored["evidence"]["records"]) == 2
    assert stored["evidence"]["source_as_of"] == source_as_of
    assert stored["committed_at"] == committed_at
    assert stored["evidence"]["source_as_of"] != stored["committed_at"]
    assert len(service.reconciliation_repository.list_history(budget_id)) == 1
    assert len(service.reconciliation_repository.list_history(tracking_id)) == 1

    with pytest.raises(duckdb.ConstraintException):
        service.create_reconciliation_commit(
            budget_id,
            {
                "reconciliation_id": budget_commit["reconciliation_id"],
                "committed_at": datetime(2026, 9, 2, tzinfo=timezone.utc),
                "evidence": {
                    "entity_id": budget_id,
                    "entity_class": "BUDGET",
                    "evidence_kind": "LIVE_BALANCE",
                    "source_adapter": "manual",
                    "source_as_of": source_as_of,
                    "normalized_payload": {"cleared_minor": 1},
                },
            },
        )
    assert service.reconciliation_repository.read_commit(budget_commit["reconciliation_id"])[
        "evidence"
    ]["normalized_payload"] == {"cleared_minor": 1000, "pending_minor": 0}

    void = service.void_reconciliation_commit(
        budget_id,
        budget_commit["reconciliation_id"],
        {"recorded_at": datetime(2026, 9, 3, tzinfo=timezone.utc), "reason": "Incorrect source"},
    )
    assert void["event_type"] == "VOID"
    history = service.reconciliation_repository.list_history(budget_id)
    assert [item["event_type"] for item in history] == ["VOID", "COMMITTED"]
    assert (
        service.reconciliation_repository.read_commit(budget_commit["reconciliation_id"])[
            "committed_at"
        ]
        == committed_at
    )
    assert tracking_commit["entity_class"] == "TRACKING"


def test_commit_and_void_linkage_validate_entity_and_class(service) -> None:
    budget_id = service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    tracking_id = service.create_account({"name": "Car", "account_class": "TRACKING"})["account_id"]
    evidence = {
        "entity_id": budget_id,
        "entity_class": "BUDGET",
        "evidence_kind": "LIVE_BALANCE",
        "source_adapter": "manual",
        "source_as_of": datetime(2026, 9, 1, tzinfo=timezone.utc),
        "normalized_payload": {"value_minor": 10},
    }
    with pytest.raises(ValueError, match="linkage"):
        service.create_reconciliation_commit(tracking_id, {"evidence": evidence})
    commit = service.create_reconciliation_commit(
        budget_id,
        {"committed_at": datetime(2026, 9, 2, tzinfo=timezone.utc), "evidence": evidence},
    )
    with pytest.raises(ValueError, match="class"):
        service.reconciliation_repository.void_commit(
            reconciliation_id=commit["reconciliation_id"],
            entity_id=budget_id,
            entity_class="TRACKING",
            recorded_at=datetime(2026, 9, 3, tzinfo=timezone.utc),
        )


def test_reconciliation_ending_value_includes_opening_history(service) -> None:
    account_id = service.create_account(
        {"name": "Savings", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    service.create_transaction(
        {
            "date": date(2026, 7, 31),
            "account_id": account_id,
            "amount_minor": 1_000,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "Opening history",
        }
    )
    period_transaction_id = service.create_transaction(
        {
            "date": date(2026, 8, 10),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "Period inflow",
        }
    )["transaction_id"]

    draft = service.create_reconciliation_draft(
        account_id,
        {
            "source_kind": "BANK_STATEMENT",
            "period_start": date(2026, 8, 1),
            "cutoff": date(2026, 8, 31),
            "source_ending_value_minor": 1_100,
            "source_records": [
                {
                    "source_record_id": "period-1",
                    "transaction_id": period_transaction_id,
                    "posted_date": date(2026, 8, 10),
                    "signed_amount_minor": 100,
                    "source_status": "CLEARED",
                }
            ],
        },
    )

    assert draft["ledger_value_minor"] == 1_100
    assert draft["difference_minor"] == 0
    assert draft["classifications"]["local_only"] == []
    committed = service.apply_reconciliation(
        draft["reconciliation_id"], {"client_operation_id": str(uuid4())}
    )
    assert committed["state"] == "SUCCESSFUL"
    assert service.db.fetch_one(
        "SELECT COUNT(*) AS count FROM reconciliation_transaction_refs WHERE reconciliation_id = ?",
        (draft["reconciliation_id"],),
    ) == {"count": 2}


def test_investment_reconciliation_uses_statement_value(service) -> None:
    investment_id = service.create_account({"name": "Brokerage", "account_class": "INVESTMENT"})[
        "account_id"
    ]
    service.reconcile_investment_statement(
        investment_id,
        {
            "effective_date": service.clock.today(),
            "cash_balance_minor": 1_000,
            "holdings": [],
        },
    )

    draft = service.create_reconciliation_draft(
        investment_id,
        {
            "source_kind": "INVESTMENT_STATEMENT",
            "cutoff": service.clock.today(),
            "source_ending_value_minor": 1_000,
        },
    )

    assert draft["ledger_value_minor"] == 1_000
    assert draft["difference_minor"] == 0


def _budget_account(service, name: str = "Checking") -> str:
    return service.create_account(
        {"name": name, "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]


def _commit_budget_baseline(service, account_id: str) -> dict[str, object]:
    return service.create_reconciliation_commit(
        account_id,
        {
            "committed_at": service.clock.now(),
            "evidence": {
                "entity_id": account_id,
                "entity_class": "BUDGET",
                "evidence_kind": "LIVE_BALANCE",
                "source_adapter": "manual",
                "source_as_of": service.clock.now(),
                "normalized_payload": {"cleared_minor": 0, "pending_minor": 0},
            },
        },
    )


def _current_transaction(service, transaction_id: str) -> dict[str, object]:
    row = service.db.fetch_one(
        "SELECT * FROM current_transactions WHERE transaction_id = ?", (transaction_id,)
    )
    assert row is not None
    return row


def _update_transaction(service, transaction_id: str, **changes: object) -> None:
    current = _current_transaction(service, transaction_id)
    payload = {
        "expected_version": str(current["row_id"]),
        "date": current["date"],
        "account_id": str(current["account_id"]),
        "amount_minor": current["amount_minor"],
        "category_id": current["category_id"],
        "system_category": current["system_category"],
        "status": current["status"],
        "memo": current["memo"],
    }
    payload.update(changes)
    service.update_transaction(transaction_id, payload)


def test_working_set_classifies_logical_changes_and_ignores_metadata(service) -> None:
    account_id = _budget_account(service)
    cleared_id = service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "cleared",
        }
    )["transaction_id"]
    pending_id = service.create_transaction(
        {
            "date": date(2026, 2, 2),
            "account_id": account_id,
            "amount_minor": -25,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "PENDING",
            "memo": "pending",
        }
    )["transaction_id"]
    _commit_budget_baseline(service, account_id)

    unchanged_pending = service.reconciliation_working_set(account_id)
    assert [
        (item["transaction_id"], item["classification"]) for item in unchanged_pending["items"]
    ] == [(pending_id, "CARRIED_PENDING")]

    _update_transaction(
        service,
        cleared_id,
        category_id=str(uuid4()),
        system_category=None,
        memo="metadata only",
    )
    assert service.reconciliation_working_set(account_id)["items"] == unchanged_pending["items"]

    service.clock.advance(minutes=1)
    _update_transaction(service, cleared_id, amount_minor=125)
    _update_transaction(service, pending_id, status="CLEARED")
    items = service.reconciliation_working_set(account_id)["items"]
    by_id = {item["transaction_id"]: item for item in items}
    assert by_id[cleared_id]["classification"] == "EDITED"
    assert by_id[cleared_id]["changed_fields"] == ["amount_minor"]
    assert by_id[pending_id]["classification"] == "PENDING_CLEARED"
    assert len(items) == 2


def test_working_set_backdated_create_removed_and_restored(service) -> None:
    account_id = _budget_account(service)
    original_id = service.create_transaction(
        {
            "date": date(2026, 2, 10),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )["transaction_id"]
    _commit_budget_baseline(service, account_id)
    service.clock.advance(minutes=1)

    backdated_id = service.create_transaction(
        {
            "date": date(2026, 1, 1),
            "account_id": account_id,
            "amount_minor": 50,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )["transaction_id"]
    backdated = service.reconciliation_working_set(account_id)["items"]
    assert [item["transaction_id"] for item in backdated] == [backdated_id]
    assert backdated[0]["classification"] == "NEW"

    original = _current_transaction(service, original_id)
    service.delete_transaction(original_id, str(original["row_id"]))
    removed = service.reconciliation_working_set(account_id)["items"]
    removed_by_id = {item["transaction_id"]: item for item in removed}
    assert removed_by_id[original_id]["classification"] == "REMOVED"
    assert removed_by_id[original_id]["current"] is None

    _commit_budget_baseline(service, account_id)
    service.clock.advance(minutes=1)
    service.restore_transaction(original_id)
    restored = service.reconciliation_working_set(account_id)["items"]
    restored_by_id = {item["transaction_id"]: item for item in restored}
    assert restored_by_id[original_id]["classification"] == "RESTORED"
    assert backdated_id not in restored_by_id


def test_account_move_round_trip_is_not_a_restore(service) -> None:
    account_a = _budget_account(service, "A")
    account_b = _budget_account(service, "B")
    transaction_id = service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_b,
            "amount_minor": 100,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "CLEARED",
        }
    )["transaction_id"]
    _update_transaction(service, transaction_id, account_id=account_a)
    _commit_budget_baseline(service, account_b)
    _update_transaction(service, transaction_id, account_id=account_b)

    items = service.reconciliation_working_set(account_b)["items"]
    assert len(items) == 1
    assert items[0]["transaction_id"] == transaction_id
    assert items[0]["classification"] == "NEW"


def test_delete_and_restore_at_same_clock_time_is_restored(service) -> None:
    account_id = _budget_account(service)
    transaction_id = service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )["transaction_id"]
    _commit_budget_baseline(service, account_id)
    current = _current_transaction(service, transaction_id)
    service.delete_transaction(transaction_id, str(current["row_id"]))
    service.clock.advance(microseconds=1)
    _commit_budget_baseline(service, account_id)
    service.clock.advance(microseconds=-1)
    service.restore_transaction(transaction_id)

    items = service.reconciliation_working_set(account_id)["items"]
    assert len(items) == 1
    assert items[0]["transaction_id"] == transaction_id
    assert items[0]["classification"] == "RESTORED"
    _update_transaction(service, transaction_id, memo="edited after restore")
    versions = service.db.fetch_all(
        "SELECT valid_from, valid_to FROM transactions WHERE transaction_id = ? ORDER BY valid_from",
        (transaction_id,),
    )
    assert all(
        left["valid_to"] <= right["valid_from"]
        for left, right in zip(versions, versions[1:], strict=False)
    )


def test_post_baseline_create_remove_restore_is_restored_not_new(service) -> None:
    account_id = _budget_account(service)
    _commit_budget_baseline(service, account_id)
    transaction_id = service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )["transaction_id"]
    current = _current_transaction(service, transaction_id)
    service.delete_transaction(transaction_id, str(current["row_id"]))
    service.restore_transaction(transaction_id)

    items = service.reconciliation_working_set(account_id)["items"]
    assert len(items) == 1
    assert items[0]["transaction_id"] == transaction_id
    assert items[0]["classification"] == "RESTORED"


def test_working_set_is_account_local_and_does_not_pair_independent_records(service) -> None:
    account_a = _budget_account(service, "A")
    account_b = _budget_account(service, "B")
    outgoing_id = service.create_transaction(
        {
            "date": date(2026, 2, 10),
            "account_id": account_a,
            "amount_minor": -100,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "CLEARED",
        }
    )["transaction_id"]
    _commit_budget_baseline(service, account_a)
    _commit_budget_baseline(service, account_b)
    incoming_id = service.create_transaction(
        {
            "date": date(2026, 2, 10),
            "account_id": account_b,
            "amount_minor": 100,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "CLEARED",
        }
    )["transaction_id"]

    a_items = service.reconciliation_working_set(account_a)["items"]
    b_items = service.reconciliation_working_set(account_b)["items"]
    assert a_items == []
    assert [item["transaction_id"] for item in b_items] == [incoming_id]
    assert service.db.fetch_all("SELECT * FROM current_transaction_operation_legs") == []

    _update_transaction(service, outgoing_id, account_id=account_b)
    assert service.reconciliation_working_set(account_a)["items"][0]["classification"] == "REMOVED"
    b_by_id = {
        item["transaction_id"]: item
        for item in service.reconciliation_working_set(account_b)["items"]
    }
    assert b_by_id[outgoing_id]["classification"] == "NEW"


def test_working_set_observes_both_legs_of_provenance_backed_operation(service) -> None:
    checking_id = _budget_account(service, "Checking")
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
    investment_id = service.create_account(
        {
            "name": "Brokerage",
            "account_class": "INVESTMENT",
            "investment_contribution_category_id": category_id,
        }
    )["account_id"]
    service.reconcile_investment_statement(
        investment_id,
        {"effective_date": service.clock.today(), "cash_balance_minor": 0, "holdings": []},
    )
    _commit_budget_baseline(service, checking_id)
    service.create_reconciliation_commit(
        investment_id,
        {
            "committed_at": service.clock.now(),
            "evidence": {
                "entity_id": investment_id,
                "entity_class": "INVESTMENT",
                "evidence_kind": "VALUATION_SNAPSHOT",
                "source_adapter": "manual",
                "source_as_of": service.clock.now(),
                "normalized_payload": {"value_minor": 0},
            },
        },
    )

    operation = service.create_investment_transfer(
        investment_id,
        {
            "direction": "CONTRIBUTION",
            "client_operation_id": str(uuid4()),
            "source_account_id": checking_id,
            "source_posted_date": service.clock.today(),
            "source_status": "CLEARED",
            "destination_account_id": investment_id,
            "destination_posted_date": service.clock.today(),
            "destination_status": "CLEARED",
            "amount_minor": 1_000,
            "memo": "Contribution",
        },
    )
    operation_legs = service.db.fetch_all(
        "SELECT * FROM current_transaction_operation_legs WHERE operation_id = ?",
        (operation["operation_id"],),
    )
    assert {str(row["transaction_id"]) for row in operation_legs} == {
        operation["source_transaction_id"],
        operation["destination_transaction_id"],
    }
    assert {
        item["transaction_id"] for item in service.reconciliation_working_set(checking_id)["items"]
    } == {operation["source_transaction_id"]}
    assert {
        item["transaction_id"]
        for item in service.reconciliation_working_set(investment_id)["items"]
    } == {operation["destination_transaction_id"]}


def test_successive_complete_baseline_keeps_unchanged_old_transaction(service) -> None:
    account_id = _budget_account(service)
    old_id = service.create_transaction(
        {
            "date": date(2026, 1, 1),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )["transaction_id"]
    first = _commit_budget_baseline(service, account_id)
    first_ref = service.db.fetch_one(
        "SELECT * FROM reconciliation_transaction_refs WHERE reconciliation_id = ?",
        (first["reconciliation_id"],),
    )
    assert first_ref is not None

    service.clock.advance(minutes=1)
    service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_id,
            "amount_minor": 25,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
        }
    )
    second = _commit_budget_baseline(service, account_id)
    refs = service.db.fetch_all(
        "SELECT * FROM reconciliation_transaction_refs WHERE reconciliation_id = ?",
        (second["reconciliation_id"],),
    )
    assert len(refs) == 2
    assert {str(ref["transaction_id"]) for ref in refs} == {
        old_id,
        str(next(ref["transaction_id"] for ref in refs if str(ref["transaction_id"]) != old_id)),
    }
    old_ref = next(ref for ref in refs if str(ref["transaction_id"]) == old_id)
    assert old_ref["valid_from"] == first_ref["valid_from"]


def test_large_budget_baseline_uses_bulk_capture_and_resolution(service, monkeypatch) -> None:
    account_id = _budget_account(service)
    now = service.clock.now()
    rows = [
        {
            "row_id": str(uuid4()),
            "transaction_id": str(uuid4()),
            "date": date(2026, 1, 1),
            "account_id": account_id,
            "amount_minor": index,
            "category_id": None,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "migrated",
            "entry_order": index,
            "record_order": None,
            "valid_from": now,
            "valid_to": MAX_TS,
            "created_at": now,
            "created_by_user_id": None,
        }
        for index in range(1, 1_501)
    ]
    with service.db.transaction() as connection:
        batch_insert_versions(connection, "transactions", rows, batch_size=500)

    commit = _commit_budget_baseline(service, account_id)
    assert service.db.fetch_one(
        "SELECT COUNT(*) AS count FROM reconciliation_transaction_refs WHERE reconciliation_id = ?",
        (commit["reconciliation_id"],),
    ) == {"count": 1_500}

    original_fetch_all = service.db.fetch_all
    query_count = 0

    def counted_fetch_all(query: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        nonlocal query_count
        query_count += 1
        return original_fetch_all(query, params)

    monkeypatch.setattr(service.db, "fetch_all", counted_fetch_all)
    result = service.reconciliation_working_set(account_id)
    assert result["items"] == []
    assert query_count <= 6


def test_working_set_collapses_multiple_intermediate_versions_to_one_tombstone(service) -> None:
    account_id = _budget_account(service)
    transaction_id = service.create_transaction(
        {
            "date": date(2026, 2, 1),
            "account_id": account_id,
            "amount_minor": 100,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "PENDING",
        }
    )["transaction_id"]
    _commit_budget_baseline(service, account_id)
    service.clock.advance(minutes=1)
    _update_transaction(service, transaction_id, status="CLEARED", amount_minor=125)
    service.clock.advance(minutes=1)
    _update_transaction(service, transaction_id, date=date(2026, 2, 3), amount_minor=150)
    current = _current_transaction(service, transaction_id)
    service.delete_transaction(transaction_id, str(current["row_id"]))

    items = service.reconciliation_working_set(account_id)["items"]
    assert len(items) == 1
    assert items[0]["transaction_id"] == transaction_id
    assert items[0]["classification"] == "REMOVED"


def _synthetic_transaction(
    transaction_id: str,
    *,
    valid_from: datetime,
    posted_date: date,
    amount_minor: int,
    status: str,
    account_id: str = "account-a",
    category_id: str | None = None,
    memo: str = "",
    valid_to: datetime | str = "9999-12-31T23:59:59+00:00",
) -> dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "row_id": f"row-{transaction_id}-{valid_from.isoformat()}",
        "account_id": account_id,
        "date": posted_date,
        "amount_minor": amount_minor,
        "category_id": category_id,
        "system_category": "TX_AVAILABLE_TO_BUDGET",
        "status": status,
        "memo": memo,
        "entry_order": 1,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "created_at": valid_from,
    }


@settings(max_examples=30, derandomize=True, deadline=None)
@given(
    operations=st.lists(
        st.sampled_from(
            [
                "create",
                "backdated_create",
                "amount_edit",
                "date_edit",
                "account_change",
                "pending_to_cleared",
                "cleared_to_pending",
                "category_edit",
                "memo_edit",
                "remove",
                "restore",
                "repeated_edit",
                "reconcile",
            ]
        ),
        min_size=1,
        max_size=25,
    )
)
def test_working_set_properties_over_generated_logical_histories(
    operations: list[str],
) -> None:
    baseline_committed_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
    current_time = baseline_committed_at
    baseline_pending = _synthetic_transaction(
        "baseline-pending",
        valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        posted_date=date(2026, 1, 31),
        amount_minor=-25,
        status="PENDING",
    )
    baseline_cleared = _synthetic_transaction(
        "baseline-cleared",
        valid_from=datetime(2026, 1, 2, tzinfo=timezone.utc),
        posted_date=date(2026, 1, 30),
        amount_minor=100,
        status="CLEARED",
    )
    restored_history = _synthetic_transaction(
        "historical-restore",
        valid_from=datetime(2026, 1, 3, tzinfo=timezone.utc),
        posted_date=date(2026, 1, 29),
        amount_minor=75,
        status="CLEARED",
        valid_to=datetime(2026, 1, 20, tzinfo=timezone.utc),
    )
    baseline_rows = [dict(baseline_pending), dict(baseline_cleared)]
    current_by_id = {row["transaction_id"]: dict(row) for row in baseline_rows}
    historical_rows: list[dict[str, object]] = [restored_history]
    next_id = 0
    commit_snapshots: list[tuple[list[dict[str, object]], list[dict[str, object]]]] = []

    def advance() -> datetime:
        nonlocal current_time
        current_time += timedelta(minutes=1)
        return current_time

    def edit(transaction_id: str, **changes: object) -> None:
        current = current_by_id.get(transaction_id)
        if current is None:
            return
        changed_at = advance()
        historical_rows.append(current | {"valid_to": changed_at})
        current_by_id[transaction_id] = current | {"valid_from": changed_at, **changes}

    for operation in operations:
        if operation in {"create", "backdated_create"}:
            next_id += 1
            transaction_id = f"created-{next_id}"
            edit_date = date(2025, 12, 31) if operation == "backdated_create" else date(2026, 2, 2)
            created_at = advance()
            current_by_id[transaction_id] = _synthetic_transaction(
                transaction_id,
                valid_from=created_at,
                posted_date=edit_date,
                amount_minor=10 + next_id,
                status="CLEARED",
            )
        elif operation == "amount_edit":
            edit("baseline-cleared", amount_minor=200)
        elif operation == "date_edit":
            edit("baseline-cleared", date=date(2026, 2, 3))
        elif operation == "account_change":
            edit("baseline-cleared", account_id="account-b")
        elif operation == "pending_to_cleared":
            edit("baseline-pending", status="CLEARED")
        elif operation == "cleared_to_pending":
            edit("baseline-cleared", status="PENDING")
        elif operation == "category_edit":
            edit("baseline-cleared", category_id="category-1")
        elif operation == "memo_edit":
            edit("baseline-cleared", memo="edited metadata")
        elif operation == "remove":
            transaction_id = "baseline-cleared"
            current = current_by_id.pop(transaction_id, None)
            if current is not None:
                historical_rows.append(current | {"valid_to": advance()})
        elif operation == "restore":
            if "historical-restore" not in current_by_id:
                restored_at = advance()
                current_by_id["historical-restore"] = restored_history | {
                    "valid_from": restored_at,
                    "valid_to": "9999-12-31T23:59:59+00:00",
                }
        elif operation == "repeated_edit":
            edit("baseline-cleared", amount_minor=300)
            edit("baseline-cleared", amount_minor=301)
        elif operation == "reconcile":
            baseline_rows = [dict(row) for row in current_by_id.values()]
            baseline_committed_at = advance()
            commit_snapshots.append(
                (
                    [dict(row) for row in baseline_rows],
                    [dict(row) for row in current_by_id.values()],
                )
            )

    baseline_refs = [
        {
            "transaction_id": row["transaction_id"],
            "valid_from": row["valid_from"],
            "account_id": row["account_id"],
        }
        for row in baseline_rows
    ]
    items = resolve_transaction_working_set(
        baseline_refs,
        baseline_rows,
        list(current_by_id.values()),
        historical_rows,
        baseline_committed_at=baseline_committed_at,
    )

    transaction_ids = [item["transaction_id"] for item in items]
    assert len(transaction_ids) == len(set(transaction_ids))
    for item in items:
        if item["classification"] in {"NEW", "RESTORED"}:
            assert item["baseline"] is None
            assert item["current"] is not None
        elif item["classification"] == "REMOVED":
            assert item["baseline"] is not None
            assert item["current"] is None
        else:
            assert item["baseline"] is not None
            assert item["current"] is not None
            baseline = item["baseline"]
            current = item["current"]
            changed_fields = [
                field
                for field in ("account_id", "date", "amount_minor", "status")
                if baseline[field] != current[field]
            ]
            if item["classification"] == "CARRIED_PENDING":
                assert baseline["status"] == current["status"] == "PENDING"
                assert changed_fields == []
            else:
                assert set(item["changed_fields"]) == set(changed_fields)

    for snapshot_baseline, snapshot_current in commit_snapshots:
        assert {row["transaction_id"] for row in snapshot_baseline} == {
            row["transaction_id"] for row in snapshot_current
        }
        assert {row["valid_from"] for row in snapshot_baseline} == {
            row["valid_from"] for row in snapshot_current
        }
