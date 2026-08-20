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
        } <= tables
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
