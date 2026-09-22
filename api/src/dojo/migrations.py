from __future__ import annotations

from pathlib import Path

import duckdb

from dojo.sql import load_sql


def apply_migrations(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(load_sql("schema/current"))
    _migrate_reconciliation_foundation(connection)
    _migrate_legacy_transaction_constraint(connection)
    _migrate_transaction_entry_order(connection)
    connection.execute(load_sql("schema/migrations/add_rich_account_fields"))
    connection.execute(load_sql("schema/migrations/add_backup_oauth_token"))


def _migrate_reconciliation_foundation(connection: duckdb.DuckDBPyConnection) -> None:
    columns = {
        row[0]
        for row in connection.execute(
            load_sql("queries/duckdb_columns_by_table"), ("reconciliation_commits",)
        ).fetchall()
    }
    if not columns or "entity_id" in columns:
        return

    legacy_tables = {
        row[0] for row in connection.execute(load_sql("queries/duckdb_table_names")).fetchall()
    }
    if "reconciliation_commits_legacy" not in legacy_tables:
        connection.execute(load_sql("schema/migrations/rename_legacy_reconciliation"))
    connection.execute(load_sql("schema/migrations/reconciliation_foundation"))


def provision_database(path: str) -> None:
    db_path = Path(path)
    if path != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(path)
    try:
        connection.execute(load_sql("control/set_timezone_utc"))
        apply_migrations(connection)
    finally:
        connection.close()


def _migrate_legacy_transaction_constraint(connection: duckdb.DuckDBPyConnection) -> None:
    transaction_table = connection.execute(
        load_sql("queries/duckdb_table_sql_by_name"),
        ("transactions",),
    ).fetchone()
    if transaction_table is None:
        return
    sql = str(transaction_table[0] or "")
    normalized_sql = " ".join(sql.split()).casefold()
    has_legacy_constraint = (
        "category_id is not null" in normalized_sql
        and "system_category is null" in normalized_sql
        and "category_id is null" in normalized_sql
        and "system_category is not null" in normalized_sql
        and "not (category_id is not null and system_category is not null)" not in normalized_sql
    )
    if has_legacy_constraint:
        connection.execute(load_sql("schema/migrations/legacy_transactions_constraint"))


def _migrate_transaction_entry_order(connection: duckdb.DuckDBPyConnection) -> None:
    transaction_table = connection.execute(
        load_sql("queries/duckdb_table_sql_by_name"),
        ("transactions",),
    ).fetchone()
    if transaction_table is None:
        return
    sql = str(transaction_table[0] or "")
    normalized_sql = " ".join(sql.split()).casefold()
    if "entry_order" not in normalized_sql:
        connection.execute(load_sql("schema/migrations/add_transaction_entry_order"))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Provision the current dojo DuckDB schema")
    parser.add_argument("duckdb_path")
    args = parser.parse_args()
    provision_database(args.duckdb_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
