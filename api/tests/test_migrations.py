from __future__ import annotations

from importlib import reload

import duckdb

import dojo.api.main as main_module
from dojo.api.settings import get_settings
from dojo.database import Database
from dojo.migrations import provision_database
from dojo.sql import load_sql


def test_current_migration_set_provisions_fresh_database(tmp_path) -> None:
    duckdb_path = tmp_path / "fresh.duckdb"
    provision_database(str(duckdb_path))
    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        tables = {
            row["table_name"] for row in database.fetch_all(load_sql("queries/duckdb_table_names"))
        }
        assert {
            "import_runs",
            "import_batches",
            "accounts",
            "budget_account_settings",
            "category_groups",
            "categories",
            "budget_buckets",
            "transactions",
            "allocations",
            "net_worth_valuations",
            "financial_command_receipts",
            "transaction_operations",
            "transaction_operation_legs",
            "reconciliation_evidence",
            "reconciliation_evidence_records",
            "reconciliation_commits",
            "reconciliation_history",
            "reconciliation_transaction_refs",
            "backup_configurations",
            "backup_runs",
        } <= tables

        receipt_columns = {
            row["column_name"]: row
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"),
                ("financial_command_receipts",),
            )
        }
        assert receipt_columns["client_operation_id"]["is_nullable"] is False
        assert receipt_columns["result"]["data_type"] == "JSON"

        operation_leg_columns = {
            row["column_name"]: row
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"),
                ("transaction_operation_legs",),
            )
        }
        assert {
            "operation_id",
            "transaction_id",
            "leg_role",
            "valid_from",
            "valid_to",
        } <= operation_leg_columns.keys()
        assert database.fetch_all("SELECT * FROM current_transaction_operation_legs") == []
    finally:
        database.close()


def test_legacy_reconciliation_schema_is_migrated_deterministically(tmp_path) -> None:
    duckdb_path = tmp_path / "legacy-reconciliation.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    reconciliation_id = "00000000-0000-0000-0000-000000000001"
    evidence_id = "00000000-0000-0000-0000-000000000002"
    account_id = "00000000-0000-0000-0000-000000000003"
    try:
        connection.execute(load_sql("tests/create_legacy_reconciliation_tables"))
        connection.execute(
            """
            INSERT INTO reconciliation_commits VALUES
            (?, ?, 'BUDGET', 'BANK_STATEMENT', DATE '2026-08-01', DATE '2026-08-31',
             DATE '2026-08-31', TIMESTAMPTZ '2026-09-01 10:00:00+00', 'CURRENT', ?,
             'legacy-evidence-digest', 'legacy-baseline-digest', 1000,
             TIMESTAMPTZ '2026-09-01 09:00:00+00', NULL),
            ('00000000-0000-0000-0000-000000000004', ?, 'BUDGET', 'BANK_STATEMENT',
             DATE '2026-08-01', DATE '2026-08-31', DATE '2026-08-31', NULL, 'DRAFT', ?,
             'draft-evidence-digest', 'draft-baseline-digest', 1000,
             TIMESTAMPTZ '2026-09-01 09:30:00+00', NULL)
            """,
            (
                reconciliation_id,
                account_id,
                evidence_id,
                account_id,
                "00000000-0000-0000-0000-000000000005",
            ),
        )
        connection.execute(
            """
            INSERT INTO reconciliation_source_records VALUES
            (?, 'legacy-record', NULL, 0, ?, DATE '2026-08-31', NULL, 1000,
             'CLEARED', 'Opening', 'record-digest', NULL)
            """,
            (evidence_id, account_id),
        )
    finally:
        connection.close()

    provision_database(str(duckdb_path))
    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        assert database.fetch_one("SELECT COUNT(*) AS count FROM reconciliation_commits") == {
            "count": 1
        }
        assert database.fetch_one("SELECT COUNT(*) AS count FROM reconciliation_evidence") == {
            "count": 1
        }
        assert database.fetch_one(
            "SELECT COUNT(*) AS count FROM reconciliation_evidence_records"
        ) == {"count": 1}
        assert database.fetch_one(
            "SELECT COUNT(*) AS count FROM reconciliation_history WHERE event_type = 'COMMITTED'"
        ) == {"count": 1}
        migrated_times = database.fetch_one(
            "SELECT source_as_of, committed_at FROM reconciliation_evidence "
            "JOIN reconciliation_commits USING (evidence_id)"
        )
        assert migrated_times is not None
        assert str(migrated_times["source_as_of"]).startswith("2026-08-31")
        assert str(migrated_times["committed_at"]).startswith("2026-09-01")
        assert database.fetch_one(
            "SELECT COUNT(*) AS count FROM reconciliation_commits_legacy WHERE state = 'DRAFT'"
        ) == {"count": 1}
    finally:
        database.close()


def test_importing_api_main_does_not_create_or_migrate_database(monkeypatch, tmp_path) -> None:
    duckdb_path = tmp_path / "import-only.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(duckdb_path))
    monkeypatch.setenv("SESSION_SECRET", "import-only-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    get_settings.cache_clear()
    reload(main_module)
    assert duckdb_path.exists() is False


def test_existing_database_receives_rich_account_schema(tmp_path) -> None:
    duckdb_path = tmp_path / "existing.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute(load_sql("tests/create_pre_rich_account_tables"))
    finally:
        connection.close()

    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        loan_columns = {
            row["column_name"]: row
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"), ("loan_details",)
            )
        }
        assert {
            "rate_type",
            "scheduled_principal_interest_minor",
            "payment_frequency",
            "next_payment_date",
            "maturity_date",
            "remaining_term_months",
            "recurring_extra_principal_minor",
        } <= loan_columns.keys()

        snapshot_columns = {
            row["column_name"]: row
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"), ("loan_balance_snapshots",)
            )
        }
        assert snapshot_columns["unapplied_credit_minor"]["is_nullable"] is True
        assert {"ytd_principal_paid_minor", "ytd_interest_paid_minor"} <= snapshot_columns.keys()

        assert {
            "record_order",
        } <= {
            row["column_name"]
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"),
                ("investment_cash_snapshots",),
            )
        }
        assert {
            "record_order",
        } <= {
            row["column_name"]
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"), ("transactions",)
            )
        }

        tables = {
            row["table_name"] for row in database.fetch_all(load_sql("queries/duckdb_table_names"))
        }
        assert {"tracking_cutovers", "tracking_cutover_successors"} <= tables
        null_orders = database.fetch_one(load_sql("queries/null_financial_event_order_counts"))
        assert null_orders == {"cash_snapshot_count": 0, "transaction_count": 0}
        assert len(database.fetch_all(load_sql("queries/current_financial_event_orders"))) == 2
        assert database.fetch_one(load_sql("queries/next_financial_event_order")) is not None
    finally:
        database.close()
