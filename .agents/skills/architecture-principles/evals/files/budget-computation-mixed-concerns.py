"""Eval fixture: one function mixes shell, core calculation, and formatting."""

from decimal import Decimal

import duckdb


def get_category_summary(db_path: str, category_id: str, month: str) -> dict[str, str]:
    conn = duckdb.connect(db_path)
    rows = conn.execute(
        "SELECT amount_minor FROM transactions WHERE category_id = ? AND month = ?",
        [category_id, month],
    ).fetchall()
    total_minor = sum(row[0] for row in rows)
    total = Decimal(total_minor) / Decimal(100)
    return {"category_id": category_id, "display_total": f"${total:,.2f}"}
