from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import duckdb
import pytest

from dojo.reconciliation import LocalRecord, SourceRecord, compare_records, transaction_digest


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
