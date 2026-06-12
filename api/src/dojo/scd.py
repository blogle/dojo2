from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from duckdb import DuckDBPyConnection

from dojo.constants import MAX_TS


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_predicate(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return f"{prefix}valid_to = TIMESTAMPTZ '{MAX_TS}'"


def as_of_predicate(as_of_placeholder: str = "?", alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return f"{prefix}valid_from <= {as_of_placeholder} AND {as_of_placeholder} < {prefix}valid_to"


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
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(data.values())
    )


def replace_current_version(
    connection: DuckDBPyConnection,
    table: str,
    logical_column: str,
    logical_id: str,
    replacement: dict[str, Any],
    now: datetime | None = None,
) -> None:
    timestamp = now or utc_now()
    connection.execute(
        f"UPDATE {table} SET valid_to = ? WHERE {logical_column} = ? AND valid_to = TIMESTAMPTZ '{MAX_TS}'",
        (timestamp, logical_id),
    )
    insert_version(connection, table, replacement | {"valid_from": timestamp, "valid_to": MAX_TS})


def close_current_version(
    connection: DuckDBPyConnection,
    table: str,
    logical_column: str,
    logical_id: str,
    now: datetime | None = None,
) -> None:
    timestamp = now or utc_now()
    connection.execute(
        f"UPDATE {table} SET valid_to = ? WHERE {logical_column} = ? AND valid_to = TIMESTAMPTZ '{MAX_TS}'",
        (timestamp, logical_id),
    )
