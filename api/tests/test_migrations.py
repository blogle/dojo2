from __future__ import annotations

from importlib import reload

import dojo.api.main as main_module
from dojo.api.settings import get_settings
from dojo.database import Database
from dojo.migrations import provision_database
from dojo.sql import load_sql


def test_current_migration_set_provisions_fresh_database(tmp_path) -> None:
    duckdb_path = tmp_path / "fresh.duckdb"
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
