from __future__ import annotations

import json
from contextlib import contextmanager
from threading import RLock
from typing import Any, Iterator
from uuid import UUID

import duckdb

from dojo.sql import load_sql


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
        self._connection = duckdb.connect(path)
        self._connection.execute(load_sql("control/set_timezone_utc"))
        self._lock = RLock()

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
            self._connection.execute(load_sql("control/begin"))
            try:
                yield self._connection
            except Exception:
                self._connection.execute(load_sql("control/rollback"))
                raise
            else:
                self._connection.execute(load_sql("control/commit"))
