from __future__ import annotations

from dojo.sql import load_sql


def bootstrap_sql() -> str:
    return load_sql("schema/current")


def migrate_sql() -> tuple[str, ...]:
    return (load_sql("schema/migrations/legacy_transactions_constraint"),)
