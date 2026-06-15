from __future__ import annotations

from datetime import datetime
from typing import Any

from dojo.constants import MAX_TS
from dojo.sql import render_sql


def _rows(db: Any, table: str, logical_column: str, logical_id: str) -> list[dict[str, Any]]:
    return db.fetch_all(
        render_sql(
            "templates/select_columns_where_ordered",
            columns="*",
            table=table,
            predicate=f"{logical_column} = ?",
            order_by="valid_from, created_at, row_id",
        ),
        (logical_id,),
    )


def assert_no_overlapping_versions(
    db: Any, table: str, logical_column: str, logical_id: str
) -> None:
    rows = _rows(db, table, logical_column, logical_id)
    for earlier, later in zip(rows, rows[1:], strict=False):
        assert earlier["valid_to"] <= later["valid_from"], (
            f"overlapping versions found for {table}.{logical_column}={logical_id}: "
            f"{earlier['valid_from']}..{earlier['valid_to']} overlaps {later['valid_from']}..{later['valid_to']}"
        )


def assert_single_current_version(
    db: Any, table: str, logical_column: str, logical_id: str
) -> dict[str, Any]:
    rows = db.fetch_all(
        render_sql(
            "templates/select_columns_where",
            columns="*",
            table=table,
            predicate=f"{logical_column} = ? AND valid_to = TIMESTAMPTZ '{MAX_TS}'",
        ),
        (logical_id,),
    )
    assert (
        len(rows) == 1
    ), f"expected one current version for {table}.{logical_column}={logical_id}, found {len(rows)}"
    return rows[0]


def assert_no_current_version(db: Any, table: str, logical_column: str, logical_id: str) -> None:
    rows = db.fetch_all(
        render_sql(
            "templates/select_columns_where",
            columns="*",
            table=table,
            predicate=f"{logical_column} = ? AND valid_to = TIMESTAMPTZ '{MAX_TS}'",
        ),
        (logical_id,),
    )
    assert (
        rows == []
    ), f"expected no current version for {table}.{logical_column}={logical_id}, found {len(rows)}"


def assert_as_of_version(
    db: Any,
    table: str,
    logical_column: str,
    logical_id: str,
    as_of: datetime,
    expected: dict[str, Any],
) -> dict[str, Any]:
    row = db.fetch_one(
        render_sql(
            "templates/select_columns_where",
            columns="*",
            table=table,
            predicate=f"{logical_column} = ? AND valid_from <= ? AND ? < valid_to",
        ),
        (logical_id, as_of, as_of),
    )
    assert (
        row is not None
    ), f"expected historical version for {table}.{logical_column}={logical_id} at {as_of}"
    for key, value in expected.items():
        assert row[key] == value, f"expected {key}={value!r} at {as_of}, got {row[key]!r}"
    return row


def assert_history_preserved_after_edit(
    db: Any,
    table: str,
    logical_column: str,
    logical_id: str,
    *,
    before_timestamp: datetime,
    expected_before: dict[str, Any],
    expected_current: dict[str, Any],
) -> None:
    assert_no_overlapping_versions(db, table, logical_column, logical_id)
    assert_as_of_version(db, table, logical_column, logical_id, before_timestamp, expected_before)
    current = assert_single_current_version(db, table, logical_column, logical_id)
    for key, value in expected_current.items():
        assert current[key] == value, f"expected current {key}={value!r}, got {current[key]!r}"


def assert_history_preserved_after_void(
    db: Any,
    table: str,
    logical_column: str,
    logical_id: str,
    *,
    before_timestamp: datetime,
    expected_before: dict[str, Any],
) -> None:
    assert_no_overlapping_versions(db, table, logical_column, logical_id)
    assert_as_of_version(db, table, logical_column, logical_id, before_timestamp, expected_before)
    assert_no_current_version(db, table, logical_column, logical_id)
