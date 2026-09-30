from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import duckdb

from dojo.sql import load_sql


def apply_migrations(connection: duckdb.DuckDBPyConnection) -> None:
    legacy_positions = _rename_legacy_investment_table(connection, "investment_positions")
    legacy_prices = _rename_legacy_investment_table(connection, "investment_price_snapshots")
    connection.execute(load_sql("schema/current"))
    _migrate_legacy_investments(connection, legacy_positions, legacy_prices)
    _migrate_reconciliation_foundation(connection)
    _migrate_legacy_transaction_constraint(connection)
    _migrate_transaction_entry_order(connection)
    connection.execute(load_sql("schema/migrations/add_rich_account_fields"))
    connection.execute(load_sql("schema/migrations/add_backup_oauth_token"))


def _rename_legacy_investment_table(
    connection: duckdb.DuckDBPyConnection, table_name: str
) -> str | None:
    columns = {
        row[0]
        for row in connection.execute(
            load_sql("queries/duckdb_columns_by_table"), (table_name,)
        ).fetchall()
    }
    canonical_column = "instrument_id"
    if not columns or canonical_column in columns:
        return None
    legacy_name = f"{table_name}_dojo15_legacy"
    existing_tables = {
        row[0] for row in connection.execute(load_sql("queries/duckdb_table_names")).fetchall()
    }
    if legacy_name not in existing_tables:
        connection.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")
    return legacy_name


def _legacy_instrument_id(symbol: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"dojo:investment-instrument:{symbol.strip().upper()}"))


def _migrate_legacy_investments(
    connection: duckdb.DuckDBPyConnection,
    legacy_positions: str | None,
    legacy_prices: str | None,
) -> None:
    legacy_symbols: set[str] = set()
    if legacy_positions:
        legacy_symbols.update(
            row[0]
            for row in connection.execute(
                f"SELECT DISTINCT ticker FROM {legacy_positions}"
            ).fetchall()
        )
    if legacy_prices:
        legacy_symbols.update(
            row[0]
            for row in connection.execute(f"SELECT DISTINCT ticker FROM {legacy_prices}").fetchall()
        )
    for normalized in sorted({symbol.strip().upper() for symbol in legacy_symbols}):
        source_timestamps = []
        for legacy_table in (legacy_positions, legacy_prices):
            if legacy_table:
                source_timestamps.extend(
                    row[0]
                    for row in connection.execute(
                        f"SELECT created_at FROM {legacy_table} WHERE UPPER(TRIM(ticker)) = ?",
                        (normalized,),
                    ).fetchall()
                    if row[0] is not None
                )
        created_at = min(source_timestamps) if source_timestamps else None
        connection.execute(
            """INSERT INTO investment_instruments
               (instrument_id, symbol, name, is_cash_equivalent, created_at, created_by_user_id)
               VALUES (?, ?, NULL, FALSE, COALESCE(?, CURRENT_TIMESTAMP), NULL)
               ON CONFLICT (instrument_id) DO NOTHING""",
            (_legacy_instrument_id(normalized), normalized, created_at),
        )
    if legacy_positions:
        for row in connection.execute(f"SELECT * FROM {legacy_positions}").fetchall():
            (
                row_id,
                position_id,
                account_id,
                ticker,
                effective_date,
                quantity,
                average_basis,
                valid_from,
                valid_to,
                created_at,
                created_by,
            ) = row
            product = int(quantity) * int(average_basis)
            total_basis = product // 1_000_000
            remainder = product % 1_000_000
            if remainder > 500_000 or (remainder == 500_000 and total_basis % 2):
                total_basis += 1
            connection.execute(
                """INSERT INTO investment_positions
                   (row_id, position_id, account_id, instrument_id, effective_date,
                    quantity_micros, total_cost_basis_minor, valid_from, valid_to,
                    created_at, created_by_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (row_id) DO NOTHING""",
                (
                    row_id,
                    position_id,
                    account_id,
                    _legacy_instrument_id(ticker),
                    effective_date,
                    quantity,
                    total_basis,
                    valid_from,
                    valid_to,
                    created_at,
                    created_by,
                ),
            )
    if legacy_prices:
        for row in connection.execute(f"SELECT * FROM {legacy_prices}").fetchall():
            (
                row_id,
                snapshot_id,
                account_id,
                ticker,
                effective_date,
                price,
                source,
                valid_from,
                valid_to,
                created_at,
                created_by,
            ) = row
            connection.execute(
                """INSERT INTO investment_price_snapshots
                   (row_id, snapshot_id, account_id, instrument_id, effective_date,
                    price_minor, source, valid_from, valid_to, created_at, created_by_user_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (row_id) DO NOTHING""",
                (
                    row_id,
                    snapshot_id,
                    account_id,
                    _legacy_instrument_id(ticker),
                    effective_date,
                    price,
                    source,
                    valid_from,
                    valid_to,
                    created_at,
                    created_by,
                ),
            )
    if legacy_positions or legacy_prices:
        connection.execute(load_sql("schema/migrations/dojo15_finalize_investment_normalization"))


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
