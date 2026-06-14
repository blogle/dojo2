from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from dojo.constants import MAX_TS
from dojo.database import Database
from dojo.migrations import apply_migrations
from dojo.scd import (
    as_of_predicate,
    close_current_version,
    current_predicate,
    insert_version,
    replace_current_version,
)

ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_scd_current_and_as_of_query_semantics() -> None:
    database = Database(":memory:")
    try:
        apply_migrations(database.connection)
        with database.transaction() as connection:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": ACCOUNT_ID,
                    "account_class": "BUDGET",
                    "name": "Checking",
                    "is_hidden": False,
                    "is_active": True,
                    "metadata": "{}",
                    "valid_from": ts("2026-01-01T00:00:00+00:00"),
                    "valid_to": ts("2026-02-01T00:00:00+00:00"),
                    "created_at": ts("2026-01-01T00:00:00+00:00"),
                    "created_by_user_id": None,
                },
            )
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": ACCOUNT_ID,
                    "account_class": "BUDGET",
                    "name": "Checking Updated",
                    "is_hidden": False,
                    "is_active": True,
                    "metadata": "{}",
                    "valid_from": ts("2026-02-01T00:00:00+00:00"),
                    "valid_to": ts("9999-12-31T23:59:59+00:00"),
                    "created_at": ts("2026-01-01T00:00:00+00:00"),
                    "created_by_user_id": None,
                },
            )

        current = database.fetch_one(f"SELECT name FROM accounts WHERE {current_predicate()}")
        january = database.fetch_one(
            f"SELECT name FROM accounts WHERE {as_of_predicate(alias='accounts', as_of_placeholder='?')}",
            (ts("2026-01-15T00:00:00+00:00"), ts("2026-01-15T00:00:00+00:00")),
        )
        february = database.fetch_one(
            f"SELECT name FROM accounts WHERE {as_of_predicate(alias='accounts', as_of_placeholder='?')}",
            (ts("2026-02-15T00:00:00+00:00"), ts("2026-02-15T00:00:00+00:00")),
        )

        assert current == {"name": "Checking Updated"}
        assert january == {"name": "Checking"}
        assert february == {"name": "Checking Updated"}
    finally:
        database.close()


def test_scd_edit_semantics() -> None:
    database = Database(":memory:")
    try:
        apply_migrations(database.connection)
        with database.transaction() as connection:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": ACCOUNT_ID,
                    "account_class": "BUDGET",
                    "name": "Checking",
                    "is_hidden": False,
                    "is_active": True,
                    "metadata": "{}",
                    "valid_from": ts("2026-01-01T00:00:00+00:00"),
                    "valid_to": ts("9999-12-31T23:59:59+00:00"),
                    "created_at": ts("2026-01-01T00:00:00+00:00"),
                    "created_by_user_id": None,
                },
            )
            replace_current_version(
                connection,
                "accounts",
                "account_id",
                ACCOUNT_ID,
                {
                    "account_id": ACCOUNT_ID,
                    "account_class": "BUDGET",
                    "name": "Checking Prime",
                    "is_hidden": False,
                    "is_active": True,
                    "metadata": "{}",
                    "created_at": ts("2026-01-01T00:00:00+00:00"),
                    "created_by_user_id": None,
                },
                now=ts("2026-02-01T00:00:00+00:00"),
            )

        rows = database.fetch_all("SELECT name, valid_to FROM accounts ORDER BY valid_from")
        assert rows[0]["name"] == "Checking"
        assert rows[1]["name"] == "Checking Prime"
        assert rows[1]["valid_to"] == ts(MAX_TS.replace(" ", "T"))
    finally:
        database.close()


def test_scd_delete_semantics() -> None:
    database = Database(":memory:")
    try:
        apply_migrations(database.connection)
        with database.transaction() as connection:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": ACCOUNT_ID,
                    "account_class": "BUDGET",
                    "name": "Checking",
                    "is_hidden": False,
                    "is_active": True,
                    "metadata": "{}",
                    "valid_from": ts("2026-01-01T00:00:00+00:00"),
                    "valid_to": ts("9999-12-31T23:59:59+00:00"),
                    "created_at": ts("2026-01-01T00:00:00+00:00"),
                    "created_by_user_id": None,
                },
            )
            close_current_version(
                connection,
                "accounts",
                "account_id",
                ACCOUNT_ID,
                now=ts("2026-02-01T00:00:00+00:00"),
            )

        assert database.fetch_one(f"SELECT name FROM accounts WHERE {current_predicate()}") is None
        historical = database.fetch_one(
            f"SELECT name FROM accounts WHERE {as_of_predicate(alias='accounts', as_of_placeholder='?')}",
            (ts("2026-01-15T00:00:00+00:00"), ts("2026-01-15T00:00:00+00:00")),
        )
        assert historical == {"name": "Checking"}
    finally:
        database.close()


def test_database_migrates_legacy_transaction_category_constraint(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-transactions.duckdb"
    connection = duckdb.connect(str(db_path))
    try:
        connection.execute(
            """
CREATE TABLE transactions (
    row_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    date DATE NOT NULL,
    account_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    category_id UUID,
    system_category TEXT,
    status TEXT NOT NULL,
    memo TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (
        (category_id IS NOT NULL AND system_category IS NULL)
        OR
        (category_id IS NULL AND system_category IS NOT NULL)
    )
)
"""
        )
    finally:
        connection.close()

    connection = duckdb.connect(str(db_path))
    try:
        apply_migrations(connection)
    finally:
        connection.close()

    database = Database(str(db_path))
    try:
        transaction_table = database.fetch_one(
            "SELECT sql FROM duckdb_tables() WHERE table_name = 'transactions'"
        )
        assert transaction_table is not None
        sql = re.sub(r"\s+", " ", str(transaction_table["sql"]))
        assert "NOT ((category_id IS NOT NULL) AND (system_category IS NOT NULL))" in sql
        assert "(category_id IS NOT NULL AND system_category IS NULL)" not in sql
    finally:
        database.close()
