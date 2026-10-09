from __future__ import annotations

from importlib import reload

import duckdb
import pytest

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
        instrument_columns = {
            row["column_name"]: row
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"), ("investment_positions",)
            )
        }
        assert instrument_columns["instrument_id"]["is_nullable"] is False
        assert instrument_columns["total_cost_basis_minor"]["is_nullable"] is False
        assert "ticker" not in instrument_columns
        price_columns = {
            row["column_name"]
            for row in database.fetch_all(
                load_sql("queries/duckdb_columns_by_table"), ("investment_price_snapshots",)
            )
        }
        assert "instrument_id" in price_columns
        assert "ticker" not in price_columns
    finally:
        database.close()


def test_fresh_transaction_schema_requires_exactly_one_category_target(tmp_path) -> None:
    duckdb_path = tmp_path / "transaction-category-invariant.duckdb"
    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    insert = """INSERT INTO transactions
        (row_id, transaction_id, date, account_id, amount_minor, category_id,
         system_category, status, memo, entry_order, record_order, valid_from,
         valid_to, created_at, created_by_user_id)
        VALUES (?, ?, DATE '2026-10-01', ?, -100, ?, ?, 'PENDING', '', 1, 1,
                TIMESTAMPTZ '2026-10-01 00:00:00+00',
                TIMESTAMPTZ '9999-12-31 23:59:59+00',
                TIMESTAMPTZ '2026-10-01 00:00:00+00', NULL)"""
    try:
        for suffix, category_id, system_category in (
            ("missing", None, None),
            ("ambiguous", "00000000-0000-0000-0000-000000000001", "TX_UNCATEGORIZED"),
        ):
            with pytest.raises(duckdb.ConstraintException):
                database.connection.execute(
                    insert,
                    (
                        f"00000000-0000-0000-0000-00000000000{2 if suffix == 'missing' else 3}",
                        f"00000000-0000-0000-0000-00000000001{2 if suffix == 'missing' else 3}",
                        "00000000-0000-0000-0000-000000000004",
                        category_id,
                        system_category,
                    ),
                )
        database.connection.execute(
            insert,
            (
                "00000000-0000-0000-0000-000000000005",
                "00000000-0000-0000-0000-000000000015",
                "00000000-0000-0000-0000-000000000004",
                None,
                "TX_UNCATEGORIZED",
            ),
        )
        assert database.fetch_one("SELECT COUNT(*) AS count FROM current_transactions") == {
            "count": 1
        }
    finally:
        database.close()


def test_legacy_investments_migrate_to_shared_deterministic_instruments(tmp_path) -> None:
    duckdb_path = tmp_path / "legacy-investments.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute("""
            CREATE TABLE investment_positions (
                row_id UUID, position_id UUID, account_id UUID, ticker TEXT,
                effective_date DATE, quantity_micros BIGINT, average_basis_minor BIGINT,
                valid_from TIMESTAMPTZ, valid_to TIMESTAMPTZ, created_at TIMESTAMPTZ,
                created_by_user_id UUID
            )
        """)
        connection.execute("""
            CREATE TABLE investment_price_snapshots (
                row_id UUID, snapshot_id UUID, account_id UUID, ticker TEXT,
                effective_date DATE, price_minor BIGINT, source TEXT,
                valid_from TIMESTAMPTZ, valid_to TIMESTAMPTZ, created_at TIMESTAMPTZ,
                created_by_user_id UUID
            )
        """)
        connection.execute("""
            INSERT INTO investment_positions VALUES
            ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011',
             '00000000-0000-0000-0000-000000000021', 'vti', DATE '2026-01-01', 2500000, 8000,
             TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL),
            ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000012',
             '00000000-0000-0000-0000-000000000022', 'VTI', DATE '2026-01-01', 1000000, 9000,
             TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL)
        """)
        connection.execute("""
            INSERT INTO investment_price_snapshots VALUES
            ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000013',
             NULL, 'VTI', DATE '2026-01-01', 10000, 'statement',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL)
        """)
    finally:
        connection.close()

    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        migrated = database.fetch_all("""
            SELECT p.account_id, p.instrument_id, p.total_cost_basis_minor, i.symbol
            FROM investment_positions p JOIN investment_instruments i USING (instrument_id)
            ORDER BY p.account_id
        """)
        assert [item["total_cost_basis_minor"] for item in migrated] == [20000, 9000]
        assert migrated[0]["instrument_id"] == migrated[1]["instrument_id"]
        assert migrated[0]["symbol"] == "VTI"
        assert database.fetch_one("SELECT instrument_id FROM investment_price_snapshots") == {
            "instrument_id": migrated[0]["instrument_id"]
        }
        before = database.fetch_all("SELECT * FROM investment_positions ORDER BY row_id")
    finally:
        database.close()
    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        assert database.fetch_all("SELECT * FROM investment_positions ORDER BY row_id") == before
        assert database.fetch_one("SELECT COUNT(*) AS count FROM investment_instruments") == {
            "count": 1
        }
    finally:
        database.close()


def test_interrupted_investment_migration_resumes_from_staging_tables(tmp_path) -> None:
    duckdb_path = tmp_path / "interrupted-investment-migration.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute("""
            CREATE TABLE investment_positions (
                row_id UUID, position_id UUID, account_id UUID, ticker TEXT,
                effective_date DATE, quantity_micros BIGINT, average_basis_minor BIGINT,
                valid_from TIMESTAMPTZ, valid_to TIMESTAMPTZ, created_at TIMESTAMPTZ,
                created_by_user_id UUID
            )
        """)
        connection.execute("""
            CREATE TABLE investment_price_snapshots (
                row_id UUID, snapshot_id UUID, account_id UUID, ticker TEXT,
                effective_date DATE, price_minor BIGINT, source TEXT,
                valid_from TIMESTAMPTZ, valid_to TIMESTAMPTZ, created_at TIMESTAMPTZ,
                created_by_user_id UUID
            )
        """)
        connection.execute("""
            INSERT INTO investment_positions VALUES
            ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000111',
             '00000000-0000-0000-0000-000000000121', 'vti', DATE '2026-01-01', 1000000, 8000,
             TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '2026-02-01 00:00:00+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL),
            ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000111',
             '00000000-0000-0000-0000-000000000121', 'VTI', DATE '2026-02-01', 1500000, 8000,
             TIMESTAMPTZ '2026-02-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL),
            ('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000112',
             '00000000-0000-0000-0000-000000000122', 'VTI', DATE '2026-02-01', 2000000, 9000,
             TIMESTAMPTZ '2026-02-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL)
        """)
        connection.execute("""
            INSERT INTO investment_price_snapshots VALUES
            ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000211',
             NULL, 'vti', DATE '2026-01-01', 10000, 'statement',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '2026-02-01 00:00:00+00',
             TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL),
            ('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000212',
             NULL, 'VTI', DATE '2026-02-01', 12000, 'statement',
             TIMESTAMPTZ '2026-02-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
             TIMESTAMPTZ '2026-02-01 00:00:00+00', NULL)
        """)
        connection.execute(
            "ALTER TABLE investment_positions RENAME TO investment_positions_dojo15_legacy"
        )
        connection.execute(
            "ALTER TABLE investment_price_snapshots RENAME TO investment_price_snapshots_dojo15_legacy"
        )
        connection.execute(load_sql("schema/current"))
    finally:
        connection.close()

    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        migrated_positions = database.fetch_all(
            "SELECT row_id, position_id, account_id, instrument_id, total_cost_basis_minor "
            "FROM investment_positions ORDER BY row_id"
        )
        migrated_prices = database.fetch_all(
            "SELECT row_id, instrument_id FROM investment_price_snapshots ORDER BY row_id"
        )
        assert len(migrated_positions) == 3
        assert {row["row_id"] for row in migrated_positions} == {
            "00000000-0000-0000-0000-000000000101",
            "00000000-0000-0000-0000-000000000102",
            "00000000-0000-0000-0000-000000000103",
        }
        assert [row["total_cost_basis_minor"] for row in migrated_positions] == [
            8000,
            12000,
            18000,
        ]
        assert len({row["instrument_id"] for row in migrated_positions}) == 1
        assert len(migrated_prices) == 2
        assert len({row["instrument_id"] for row in migrated_prices}) == 1
        assert database.fetch_one("SELECT COUNT(*) AS count FROM investment_instruments") == {
            "count": 1
        }
        tables = {
            row["table_name"] for row in database.fetch_all(load_sql("queries/duckdb_table_names"))
        }
        assert "investment_positions_dojo15_legacy" not in tables
        assert "investment_price_snapshots_dojo15_legacy" not in tables
        persisted_positions_before_retry = database.fetch_all(
            "SELECT * FROM investment_positions ORDER BY row_id"
        )
        persisted_prices_before_retry = database.fetch_all(
            "SELECT * FROM investment_price_snapshots ORDER BY row_id"
        )
    finally:
        database.close()

    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        assert database.fetch_all("SELECT * FROM investment_positions ORDER BY row_id") == (
            persisted_positions_before_retry
        )
        assert database.fetch_all("SELECT * FROM investment_price_snapshots ORDER BY row_id") == (
            persisted_prices_before_retry
        )
        assert database.fetch_one("SELECT COUNT(*) AS count FROM investment_instruments") == {
            "count": 1
        }
    finally:
        database.close()


def test_pre_dojo35_backup_runs_schema_migrates_without_losing_rows(tmp_path) -> None:
    duckdb_path = tmp_path / "pre-dojo35-backup-runs.duckdb"
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute(
            """
            CREATE TABLE backup_runs (
                backup_run_id UUID PRIMARY KEY, trigger_kind TEXT NOT NULL,
                status TEXT NOT NULL, phase TEXT NOT NULL, started_at TIMESTAMPTZ NOT NULL,
                completed_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL,
                source_snapshot TEXT, image_digest TEXT, restic_snapshot_id TEXT,
                database_sha256 TEXT, database_size_bytes BIGINT, error_message TEXT,
                CHECK (trigger_kind IN ('SCHEDULED', 'MANUAL')),
                CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
                CHECK (database_size_bytes IS NULL OR database_size_bytes >= 0)
            )
            """
        )
        connection.execute(
            "INSERT INTO backup_runs VALUES (?, 'SCHEDULED', 'FAILED', 'SNAPSHOTTING', "
            "TIMESTAMPTZ '2026-09-01 00:00:00+00', TIMESTAMPTZ '2026-09-01 00:01:00+00', "
            "TIMESTAMPTZ '2026-09-01 00:01:00+00', NULL, NULL, NULL, NULL, NULL, 'preserved')",
            ("00000000-0000-4000-8000-000000000035",),
        )
    finally:
        connection.close()

    provision_database(str(duckdb_path))
    database = Database(str(duckdb_path))
    try:
        assert database.fetch_one(
            "SELECT status, error_message FROM backup_runs WHERE backup_run_id = ?",
            ("00000000-0000-4000-8000-000000000035",),
        ) == {"status": "FAILED", "error_message": "preserved"}
        database.execute(
            "INSERT INTO backup_runs VALUES (?, 'SCHEDULED', 'SKIPPED', 'LOCKED', "
            "TIMESTAMPTZ '2026-09-02 00:00:00+00', TIMESTAMPTZ '2026-09-02 00:00:00+00', "
            "TIMESTAMPTZ '2026-09-02 00:00:00+00', NULL, NULL, NULL, NULL, NULL, 'held')",
            ("00000000-0000-4000-8000-000000000036",),
        )
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
        connection.execute(
            """INSERT INTO transactions
               (row_id, transaction_id, transfer_id, date, account_id, amount_minor,
                category_id, system_category, status, memo, entry_order, valid_from,
                valid_to, created_at, created_by_user_id)
               VALUES (
                 '30000000-0000-0000-0000-000000000001',
                 '30000000-0000-0000-0000-000000000002', NULL,
                 DATE '2026-06-26', '30000000-0000-0000-0000-000000000003', -3200,
                 NULL, NULL, 'PENDING', 'Uncategorized legacy market row', 1,
                 TIMESTAMPTZ '2026-10-01 12:00:00+00',
                 TIMESTAMPTZ '9999-12-31 23:59:59+00',
                 TIMESTAMPTZ '2026-10-01 12:00:00+00', NULL
               )"""
        )
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
        assert database.fetch_one(
            "SELECT category_id, system_category, status FROM current_transactions "
            "WHERE transaction_id = '30000000-0000-0000-0000-000000000002'"
        ) == {"category_id": None, "system_category": None, "status": "PENDING"}
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
        assert len(database.fetch_all(load_sql("queries/current_financial_event_orders"))) == 3
        assert database.fetch_one(load_sql("queries/next_financial_event_order")) is not None
    finally:
        database.close()
