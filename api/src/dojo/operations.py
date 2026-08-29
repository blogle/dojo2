"""Financially inert, SCD2 transaction-operation provenance."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from duckdb import DuckDBPyConnection

from dojo.constants import MAX_TS
from dojo.scd import close_current_version, insert_version
from dojo.sql import load_sql

LegRole = Literal["SOURCE", "DESTINATION"]


def _row(cursor: Any) -> dict[str, Any] | None:
    values = cursor.fetchone()
    if values is None:
        return None
    return dict(zip([column[0] for column in cursor.description], values, strict=True))


def create_transaction_operation(
    connection: DuckDBPyConnection,
    *,
    operation_id: UUID | str,
    operation_kind: str,
    origin: str,
    client_operation_id: UUID | str,
    request_fingerprint: str,
    created_at: datetime,
    created_by_user_id: UUID | str | None = None,
) -> None:
    connection.execute(
        load_sql("queries/insert_transaction_operation"),
        (
            UUID(str(operation_id)),
            operation_kind,
            origin,
            UUID(str(client_operation_id)),
            request_fingerprint,
            created_at,
            None if created_by_user_id is None else UUID(str(created_by_user_id)),
        ),
    )


def get_transaction_operation(
    connection: DuckDBPyConnection, operation_id: UUID | str
) -> dict[str, Any] | None:
    cursor = connection.execute(
        load_sql("queries/transaction_operation_by_id"),
        (UUID(str(operation_id)),),
    )
    return _row(cursor)


def _require_linkable(
    connection: DuckDBPyConnection,
    *,
    operation_id: UUID | str,
    transaction_id: UUID | str,
    leg_role: LegRole,
    allow_current_transaction: bool,
) -> None:
    if get_transaction_operation(connection, operation_id) is None:
        raise ValueError("Transaction operation not found")
    transaction = _row(
        connection.execute(
            load_sql("queries/current_transaction_by_id"),
            (UUID(str(transaction_id)),),
        )
    )
    if transaction is None:
        raise ValueError("Transaction not found")

    current_for_transaction = current_transaction_operation_legs(
        connection, transaction_id=transaction_id
    )
    if current_for_transaction and not allow_current_transaction:
        raise ValueError("Transaction already belongs to an operation")

    current_for_operation = current_transaction_operation_legs(
        connection, operation_id=operation_id
    )
    if any(
        row["leg_role"] == leg_role and str(row["transaction_id"]) != str(transaction_id)
        for row in current_for_operation
    ):
        raise ValueError(f"Transaction operation already has a {leg_role.lower()} leg")


def link_transaction_operation(
    connection: DuckDBPyConnection,
    *,
    operation_id: UUID | str,
    transaction_id: UUID | str,
    leg_role: LegRole,
    now: datetime,
    created_by_user_id: UUID | str | None = None,
) -> None:
    _require_linkable(
        connection,
        operation_id=operation_id,
        transaction_id=transaction_id,
        leg_role=leg_role,
        allow_current_transaction=False,
    )
    insert_version(
        connection,
        "transaction_operation_legs",
        {
            "operation_id": UUID(str(operation_id)),
            "transaction_id": UUID(str(transaction_id)),
            "leg_role": leg_role,
            "valid_from": now,
            "valid_to": MAX_TS,
            "created_at": now,
            "created_by_user_id": (
                None if created_by_user_id is None else UUID(str(created_by_user_id))
            ),
        },
    )


def unlink_transaction_operation(
    connection: DuckDBPyConnection,
    *,
    operation_id: UUID | str,
    transaction_id: UUID | str,
    now: datetime,
) -> None:
    current = current_transaction_operation_legs(connection, transaction_id=transaction_id)
    if not current or str(current[0]["operation_id"]) != str(operation_id):
        raise ValueError("Transaction operation link not found")
    close_current_version(
        connection,
        "transaction_operation_legs",
        "transaction_id",
        str(transaction_id),
        now=now,
    )


def relink_transaction_operation(
    connection: DuckDBPyConnection,
    *,
    operation_id: UUID | str,
    transaction_id: UUID | str,
    leg_role: LegRole,
    now: datetime,
    created_by_user_id: UUID | str | None = None,
) -> None:
    _require_linkable(
        connection,
        operation_id=operation_id,
        transaction_id=transaction_id,
        leg_role=leg_role,
        allow_current_transaction=True,
    )
    current = current_transaction_operation_legs(connection, transaction_id=transaction_id)
    if current:
        close_current_version(
            connection,
            "transaction_operation_legs",
            "transaction_id",
            str(transaction_id),
            now=now,
        )
    link_transaction_operation(
        connection,
        operation_id=operation_id,
        transaction_id=transaction_id,
        leg_role=leg_role,
        now=now,
        created_by_user_id=created_by_user_id,
    )


def current_transaction_operation_legs(
    connection: DuckDBPyConnection,
    *,
    transaction_id: UUID | str | None = None,
    operation_id: UUID | str | None = None,
) -> list[dict[str, Any]]:
    if transaction_id is not None and operation_id is not None:
        raise ValueError("Filter operation legs by transaction or operation, not both")
    query = load_sql(
        "queries/current_transaction_operation_legs_by_transaction"
        if transaction_id is not None
        else "queries/current_transaction_operation_legs_by_operation"
        if operation_id is not None
        else "queries/current_transaction_operation_legs"
    )
    filter_id = transaction_id if transaction_id is not None else operation_id
    params = () if filter_id is None else (UUID(str(filter_id)),)
    cursor = connection.execute(query, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


# This alias keeps the public vocabulary symmetrical with link/unlink/relink.
create_operation = create_transaction_operation
