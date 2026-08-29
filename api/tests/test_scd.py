from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import duckdb
import pytest

from dojo.commands import (
    CommandConflictError,
    canonical_request_json,
    execute_financial_command,
    request_fingerprint,
)
from dojo.constants import MAX_TS
from dojo.database import Database
from dojo.migrations import apply_migrations
from dojo.operations import (
    create_transaction_operation,
    current_transaction_operation_legs,
    link_transaction_operation,
    relink_transaction_operation,
    unlink_transaction_operation,
)
from dojo.scd import (
    as_of_predicate,
    close_current_version,
    current_predicate,
    insert_version,
    replace_current_version,
)
from dojo.sql import load_sql, render_sql

ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
TRANSACTION_IDS = (
    "22222222-2222-2222-2222-222222222221",
    "22222222-2222-2222-2222-222222222222",
    "22222222-2222-2222-2222-222222222223",
)


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def insert_test_transaction(
    connection: duckdb.DuckDBPyConnection,
    *,
    transaction_id: str,
    amount_minor: int,
    now: datetime,
) -> None:
    insert_version(
        connection,
        "transactions",
        {
            "transaction_id": transaction_id,
            "date": now.date(),
            "account_id": ACCOUNT_ID,
            "amount_minor": amount_minor,
            "category_id": None,
            "system_category": "TX_ACCOUNT_TRANSFER",
            "status": "CLEARED",
            "memo": "test transfer leg",
            "entry_order": abs(amount_minor),
            "record_order": abs(amount_minor),
            "valid_from": now,
            "valid_to": MAX_TS,
            "created_at": now,
            "created_by_user_id": None,
        },
    )


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

        current = database.fetch_one(
            render_sql(
                "templates/select_columns_where",
                columns="name",
                table="accounts",
                predicate=current_predicate(),
            )
        )
        january = database.fetch_one(
            render_sql(
                "templates/select_columns_where",
                columns="name",
                table="accounts",
                predicate=as_of_predicate(alias="accounts", as_of_placeholder="?"),
            ),
            (ts("2026-01-15T00:00:00+00:00"), ts("2026-01-15T00:00:00+00:00")),
        )
        february = database.fetch_one(
            render_sql(
                "templates/select_columns_where",
                columns="name",
                table="accounts",
                predicate=as_of_predicate(alias="accounts", as_of_placeholder="?"),
            ),
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

        rows = database.fetch_all(
            render_sql(
                "templates/select_columns_ordered",
                columns="name, valid_to",
                table="accounts",
                order_by="valid_from",
            )
        )
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

        assert (
            database.fetch_one(
                render_sql(
                    "templates/select_columns_where",
                    columns="name",
                    table="accounts",
                    predicate=current_predicate(),
                )
            )
            is None
        )
        historical = database.fetch_one(
            render_sql(
                "templates/select_columns_where",
                columns="name",
                table="accounts",
                predicate=as_of_predicate(alias="accounts", as_of_placeholder="?"),
            ),
            (ts("2026-01-15T00:00:00+00:00"), ts("2026-01-15T00:00:00+00:00")),
        )
        assert historical == {"name": "Checking"}
    finally:
        database.close()


def test_database_migrates_legacy_transaction_category_constraint(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-transactions.duckdb"
    connection = duckdb.connect(str(db_path))
    try:
        connection.execute(load_sql("tests/create_legacy_transactions_table"))
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
            load_sql("queries/duckdb_table_sql_by_name"),
            ("transactions",),
        )
        assert transaction_table is not None
        sql = re.sub(r"\s+", " ", str(transaction_table["sql"]))
        assert "NOT ((category_id IS NOT NULL) AND (system_category IS NOT NULL))" in sql
        assert "(category_id IS NOT NULL AND system_category IS NULL)" not in sql
    finally:
        database.close()


def test_financial_command_fingerprint_is_canonical_and_float_free() -> None:
    first = {
        "operation_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "date": ts("2026-02-01T12:00:00-05:00"),
        "amounts": [100, 200],
        "nested": {"b": False, "a": None},
    }
    second = {
        "nested": {"a": None, "b": False},
        "amounts": [100, 200],
        "date": ts("2026-02-01T17:00:00Z"),
        "operation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    }

    assert canonical_request_json(first) == canonical_request_json(second)
    assert request_fingerprint(command_kind="TRANSFER", request=first) == request_fingerprint(
        command_kind="TRANSFER", request=second
    )
    assert request_fingerprint(command_kind="TRANSFER", request=first) != request_fingerprint(
        command_kind="FUND_CATEGORY", request=first
    )
    with pytest.raises(TypeError, match="cannot contain floats"):
        canonical_request_json({"amount": 1.5})


def test_financial_command_replay_returns_stored_result_and_rejects_conflict() -> None:
    database = Database(":memory:")
    operation_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1")
    client_operation_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1")
    now = ts("2026-02-01T00:00:00Z")
    calls: list[str] = []

    try:
        apply_migrations(database.connection)

        def apply_once(
            connection: duckdb.DuckDBPyConnection, fingerprint: str
        ) -> dict[str, object]:
            calls.append("called")
            create_transaction_operation(
                connection,
                operation_id=operation_id,
                operation_kind="TRANSFER",
                origin="USER",
                client_operation_id=client_operation_id,
                request_fingerprint=fingerprint,
                created_at=now,
            )
            return {
                "operation_id": operation_id,
                "amount_minor": 100,
                "created_at": now,
                "transaction_ids": (TRANSACTION_IDS[0], TRANSACTION_IDS[1]),
            }

        first = execute_financial_command(
            database,
            client_operation_id=client_operation_id,
            command_kind="TRANSFER",
            request={"amount_minor": 100},
            command=apply_once,
            now=now,
        )
        replay = execute_financial_command(
            database,
            client_operation_id=client_operation_id,
            command_kind="TRANSFER",
            request={"amount_minor": 100},
            command=apply_once,
            now=now,
        )

        assert replay == first
        assert first == {
            "operation_id": str(operation_id),
            "amount_minor": 100,
            "created_at": "2026-02-01T00:00:00+00:00",
            "transaction_ids": [TRANSACTION_IDS[0], TRANSACTION_IDS[1]],
        }
        assert calls == ["called"]
        assert database.fetch_one("SELECT COUNT(*) AS count FROM financial_command_receipts") == {
            "count": 1
        }
        assert database.fetch_one("SELECT COUNT(*) AS count FROM transaction_operations") == {
            "count": 1
        }

        with pytest.raises(CommandConflictError):
            execute_financial_command(
                database,
                client_operation_id=client_operation_id,
                command_kind="TRANSFER",
                request={"amount_minor": 200},
                command=apply_once,
                now=now,
            )
        assert calls == ["called"]
    finally:
        database.close()


def test_concurrent_financial_command_executes_one_effect() -> None:
    database = Database(":memory:")
    client_operation_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2")
    operation_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2")
    now = ts("2026-02-01T00:00:00Z")
    start = Barrier(3)
    calls: list[str] = []

    try:
        apply_migrations(database.connection)

        def run_command() -> dict[str, object]:
            start.wait()

            def apply_once(
                connection: duckdb.DuckDBPyConnection, fingerprint: str
            ) -> dict[str, object]:
                calls.append("called")
                create_transaction_operation(
                    connection,
                    operation_id=operation_id,
                    operation_kind="TRANSFER",
                    origin="USER",
                    client_operation_id=client_operation_id,
                    request_fingerprint=fingerprint,
                    created_at=now,
                )
                return {"operation_id": str(operation_id)}

            return execute_financial_command(
                database,
                client_operation_id=client_operation_id,
                command_kind="TRANSFER",
                request={"amount_minor": 100},
                command=apply_once,
                now=now,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(run_command) for _ in range(2)]
            start.wait()
            results = [future.result() for future in futures]

        assert results[0] == results[1]
        assert calls == ["called"]
        assert database.fetch_one("SELECT COUNT(*) AS count FROM financial_command_receipts") == {
            "count": 1
        }
        assert database.fetch_one("SELECT COUNT(*) AS count FROM transaction_operations") == {
            "count": 1
        }
    finally:
        database.close()


def test_concurrent_connections_replay_the_committed_receipt(tmp_path: Path) -> None:
    database_path = tmp_path / "concurrent-commands.duckdb"
    first_database = Database(str(database_path))
    second_database: Database | None = None
    client_operation_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb5")
    now = ts("2026-02-01T00:00:00Z")
    mutations_ready = Barrier(2)

    try:
        apply_migrations(first_database.connection)
        second_database = Database(str(database_path))

        def run_command(database: Database) -> dict[str, object]:
            def insert_one_leg(
                connection: duckdb.DuckDBPyConnection, _fingerprint: str
            ) -> dict[str, object]:
                transaction_id = str(uuid4())
                mutations_ready.wait()
                insert_test_transaction(
                    connection,
                    transaction_id=transaction_id,
                    amount_minor=100,
                    now=now,
                )
                return {"transaction_id": transaction_id}

            return execute_financial_command(
                database,
                client_operation_id=client_operation_id,
                command_kind="CREATE_TRANSFER_LEG",
                request={"amount_minor": 100},
                command=insert_one_leg,
                now=now,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(run_command, first_database),
                executor.submit(run_command, second_database),
            ]
            results = [future.result() for future in futures]

        assert results[0] == results[1]
        assert first_database.fetch_one(
            "SELECT COUNT(*) AS count FROM financial_command_receipts"
        ) == {"count": 1}
        assert first_database.fetch_one("SELECT COUNT(*) AS count FROM current_transactions") == {
            "count": 1
        }
    finally:
        if second_database is not None:
            second_database.close()
        first_database.close()


def test_transaction_operation_link_relink_and_unlink_preserve_transactions() -> None:
    database = Database(":memory:")
    now = ts("2026-02-01T00:00:00Z")
    later = ts("2026-02-02T00:00:00Z")
    latest = ts("2026-02-03T00:00:00Z")
    first_operation = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3")
    second_operation = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4")

    try:
        apply_migrations(database.connection)
        with database.transaction() as connection:
            for transaction_id, amount in zip(TRANSACTION_IDS, (-100, 100, 200), strict=True):
                insert_test_transaction(
                    connection,
                    transaction_id=transaction_id,
                    amount_minor=amount,
                    now=now,
                )
            create_transaction_operation(
                connection,
                operation_id=first_operation,
                operation_kind="TRANSFER",
                origin="USER",
                client_operation_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3",
                request_fingerprint="first",
                created_at=now,
            )
            create_transaction_operation(
                connection,
                operation_id=second_operation,
                operation_kind="TRANSFER",
                origin="USER",
                client_operation_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb4",
                request_fingerprint="second",
                created_at=now,
            )
            link_transaction_operation(
                connection,
                operation_id=first_operation,
                transaction_id=TRANSACTION_IDS[0],
                leg_role="SOURCE",
                now=now,
            )
            link_transaction_operation(
                connection,
                operation_id=first_operation,
                transaction_id=TRANSACTION_IDS[1],
                leg_role="DESTINATION",
                now=now,
            )

        transactions_before = database.fetch_all(
            "SELECT * FROM transactions ORDER BY transaction_id, valid_from"
        )
        with database.transaction() as connection:
            with pytest.raises(ValueError, match="already has a destination"):
                link_transaction_operation(
                    connection,
                    operation_id=first_operation,
                    transaction_id=TRANSACTION_IDS[2],
                    leg_role="DESTINATION",
                    now=later,
                )
            relink_transaction_operation(
                connection,
                operation_id=second_operation,
                transaction_id=TRANSACTION_IDS[0],
                leg_role="SOURCE",
                now=later,
            )
            unlink_transaction_operation(
                connection,
                operation_id=first_operation,
                transaction_id=TRANSACTION_IDS[1],
                now=latest,
            )

        assert (
            database.fetch_all("SELECT * FROM transactions ORDER BY transaction_id, valid_from")
            == transactions_before
        )
        current_legs = current_transaction_operation_legs(database.connection)
        assert [(str(row["operation_id"]), row["leg_role"]) for row in current_legs] == [
            (str(second_operation), "SOURCE")
        ]
        source_history = database.fetch_all(
            """
            SELECT operation_id, valid_from, valid_to
            FROM transaction_operation_legs
            WHERE transaction_id = ?
            ORDER BY valid_from
            """,
            (TRANSACTION_IDS[0],),
        )
        assert [str(row["operation_id"]) for row in source_history] == [
            str(first_operation),
            str(second_operation),
        ]
        assert source_history[0]["valid_to"] == later
        assert source_history[1]["valid_to"] == ts(MAX_TS.replace(" ", "T"))
    finally:
        database.close()
