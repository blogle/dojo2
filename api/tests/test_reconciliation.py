from __future__ import annotations

from datetime import date
from uuid import uuid4

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


def test_budget_reconciliation_applies_explicit_adjustment_and_reopens(imported_service) -> None:
    account_id = imported_service.create_account(
        {"name": "Checking", "account_class": "BUDGET", "budget_account_type": "DEPOSIT"}
    )["account_id"]
    transaction_id = imported_service.create_transaction(
        {
            "date": date(2026, 8, 20),
            "account_id": account_id,
            "amount_minor": 1_000,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "Opening",
        }
    )["transaction_id"]
    draft = imported_service.create_reconciliation_draft(
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
    stored_draft = imported_service.get_reconciliation(draft["reconciliation_id"])
    assert stored_draft["classifications"]["exact_matches"] == [
        {"source_record_id": "bank-1", "transaction_id": transaction_id}
    ]
    operation_id = str(uuid4())
    result = imported_service.apply_reconciliation(
        draft["reconciliation_id"],
        {"client_operation_id": operation_id, "balance_adjustment_minor": 100},
    )
    assert result["state"] == "CURRENT"
    assert (
        imported_service.apply_reconciliation(
            draft["reconciliation_id"],
            {"client_operation_id": operation_id, "balance_adjustment_minor": 100},
        )
        == result
    )
    assert imported_service.get_reconciliation_status(account_id) == "CURRENT"
    imported_service.update_transaction(
        transaction_id,
        {
            "date": date(2026, 8, 20),
            "account_id": account_id,
            "amount_minor": 1,
            "system_category": "TX_AVAILABLE_TO_BUDGET",
            "status": "CLEARED",
            "memo": "bad",
        },
    )
    assert imported_service.get_reconciliation_status(account_id) == "REOPENED"


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
