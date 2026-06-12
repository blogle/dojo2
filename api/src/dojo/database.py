from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Iterator
from uuid import UUID

import duckdb

from dojo.schema import bootstrap_sql, migrate_sql


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    return value


def json_dumps(value: Any) -> str:
    return json.dumps(value, default=_json_default, sort_keys=True)


class Database:
    def __init__(self, path: str) -> None:
        db_path = Path(path)
        if path != ":memory:":
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = duckdb.connect(path)
        self._connection.execute("SET TimeZone = 'UTC'")
        self._lock = RLock()
        self._connection.execute(bootstrap_sql())
        self._run_schema_migrations()

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        return self._connection

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with self._lock:
            self._connection.execute(query, params)

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._lock:
            cursor = self._connection.execute(query, params)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
        return [
            dict(zip(columns, [_normalize_value(value) for value in row], strict=True))
            for row in rows
        ]

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        rows = self.fetch_all(query, params)
        if not rows:
            return None
        return rows[0]

    @contextmanager
    def transaction(self) -> Iterator[duckdb.DuckDBPyConnection]:
        with self._lock:
            self._connection.execute("BEGIN")
            try:
                yield self._connection
            except Exception:
                self._connection.execute("ROLLBACK")
                raise
            else:
                self._connection.execute("COMMIT")

    def _run_schema_migrations(self) -> None:
        transaction_table = self.fetch_one(
            "SELECT sql FROM duckdb_tables() WHERE table_name = 'transactions'"
        )
        if transaction_table is None:
            return
        sql = str(transaction_table.get("sql") or "")
        normalized_sql = re.sub(r"\s+", " ", sql).casefold()
        has_legacy_constraint = (
            "category_id is not null" in normalized_sql
            and "system_category is null" in normalized_sql
            and "category_id is null" in normalized_sql
            and "system_category is not null" in normalized_sql
            and "not (category_id is not null and system_category is not null)" not in normalized_sql
        )
        if not has_legacy_constraint:
            return
        for statement in migrate_sql():
            self._connection.execute(statement)
