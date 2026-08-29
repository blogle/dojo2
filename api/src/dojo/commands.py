"""Pure request canonicalization and the transactional command boundary."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any, cast
from uuid import UUID

import duckdb
from duckdb import DuckDBPyConnection

from dojo.database import Database, json_dumps
from dojo.sql import load_sql

CommandResult = dict[str, Any]
Command = Callable[[DuckDBPyConnection, str], CommandResult]


def _canonical_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise TypeError("financial command requests cannot contain floats")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("financial command mapping keys must be strings")
        return {key: _canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [_canonical_value(item) for item in value]
    raise TypeError(f"unsupported financial command request value: {type(value).__name__}")


def canonical_request(request: Any) -> Any:
    """Return the JSON-shaped, float-free representation used for fingerprints."""

    return _canonical_value(request)


def canonical_request_json(request: Any) -> str:
    return json.dumps(
        canonical_request(request), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def request_fingerprint(*, command_kind: str, request: Any) -> str:
    fingerprint_input = {
        "command_kind": command_kind,
        "request": canonical_request(request),
    }
    return sha256(canonical_request_json(fingerprint_input).encode("utf-8")).hexdigest()


def execute_financial_command(
    database: Database,
    *,
    client_operation_id: UUID | str,
    command_kind: str,
    request: Any,
    command: Command,
    now: datetime,
) -> CommandResult:
    """Run a command once, or return the result committed by its first run."""

    operation_id = UUID(str(client_operation_id))
    fingerprint = request_fingerprint(command_kind=command_kind, request=request)
    try:
        with database.transaction() as connection:
            cursor = connection.execute(
                load_sql("queries/financial_command_receipt_by_id"), (operation_id,)
            )
            receipt_row = cursor.fetchone()
            if receipt_row is not None:
                receipt = dict(
                    zip(
                        [column[0] for column in cursor.description],
                        receipt_row,
                        strict=True,
                    )
                )
                return _receipt_result(
                    receipt,
                    operation_id=operation_id,
                    command_kind=command_kind,
                    fingerprint=fingerprint,
                )

            result = cast(CommandResult, canonical_request(command(connection, fingerprint)))
            connection.execute(
                load_sql("queries/insert_financial_command_receipt"),
                (operation_id, command_kind, fingerprint, json_dumps(result), now),
            )
            return result
    except (duckdb.ConstraintException, duckdb.TransactionException):
        for _ in range(100):
            stored_receipt = database.fetch_one(
                load_sql("queries/financial_command_receipt_by_id"), (operation_id,)
            )
            if stored_receipt is not None:
                return _receipt_result(
                    stored_receipt,
                    operation_id=operation_id,
                    command_kind=command_kind,
                    fingerprint=fingerprint,
                )
            time.sleep(0.01)
        raise


class CommandConflictError(ValueError):
    """The operation ID was already used for different command content."""


def _receipt_result(
    receipt: Mapping[str, Any],
    *,
    operation_id: UUID,
    command_kind: str,
    fingerprint: str,
) -> CommandResult:
    if receipt["request_fingerprint"] != fingerprint or receipt["command_kind"] != command_kind:
        raise CommandConflictError(
            f"Operation {operation_id} was already used with different content for this command"
        )
    return cast(CommandResult, json.loads(receipt["result"]))
