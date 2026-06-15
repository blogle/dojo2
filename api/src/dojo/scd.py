from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from duckdb import DuckDBPyConnection

from dojo.constants import MAX_TS
from dojo.sql import render_sql


def current_predicate(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return render_sql("templates/current_predicate", prefix=prefix, max_ts=MAX_TS)


def as_of_predicate(as_of_placeholder: str = "?", alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return render_sql(
        "templates/as_of_predicate",
        prefix=prefix,
        as_of_placeholder=as_of_placeholder,
    )


def insert_version(
    connection: DuckDBPyConnection,
    table: str,
    values: dict[str, Any],
) -> None:
    data = dict(values)
    data.setdefault("row_id", str(uuid4()))
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    connection.execute(
        render_sql(
            "templates/insert_version",
            table=table,
            columns=columns,
            placeholders=placeholders,
        ),
        tuple(data.values()),
    )


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int | float):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def batch_insert_versions(
    connection: DuckDBPyConnection,
    table: str,
    rows: list[dict[str, Any]],
    *,
    batch_size: int = 500,
) -> None:
    if not rows:
        return
    columns = ", ".join(rows[0].keys())
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        values_clause = ", ".join(
            "(" + ", ".join(_sql_literal(v) for v in row.values()) + ")" for row in batch
        )
        connection.execute(
            render_sql(
                "templates/batch_insert_versions",
                table=table,
                columns=columns,
                values_clause=values_clause,
            )
        )


def replace_current_version(
    connection: DuckDBPyConnection,
    table: str,
    logical_column: str,
    logical_id: str,
    replacement: dict[str, Any],
    *,
    now: datetime,
) -> None:
    connection.execute(
        render_sql(
            "templates/close_current_version",
            table=table,
            logical_column=logical_column,
            max_ts=MAX_TS,
        ),
        (now, logical_id),
    )
    insert_version(connection, table, replacement | {"valid_from": now, "valid_to": MAX_TS})


def close_current_version(
    connection: DuckDBPyConnection,
    table: str,
    logical_column: str,
    logical_id: str,
    *,
    now: datetime,
) -> None:
    connection.execute(
        render_sql(
            "templates/close_current_version",
            table=table,
            logical_column=logical_column,
            max_ts=MAX_TS,
        ),
        (now, logical_id),
    )
