from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from importlib.metadata import version
from pathlib import Path

from dojo.clock import FrozenClock
from dojo.constants import CATEGORY_KIND_CREDIT_CARD_PAYMENT
from dojo.database import Database
from dojo.dev_fixture_accounts import add_development_accounts
from dojo.dev_fixture_scenario import MERCHANTS, MONTHLY_PLANS, development_named_ranges
from dojo.migrations import apply_migrations
from dojo.service import DojoService

FIXTURE_TIME = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)


def development_fixture_fingerprint() -> str:
    digest = hashlib.sha256(version("duckdb").encode("utf-8"))
    module_dir = Path(__file__).parent
    for source in (
        module_dir / "dev_fixture.py",
        module_dir / "dev_fixture_scenario.py",
        module_dir / "dev_fixture_accounts.py",
        module_dir / "migrations.py",
        module_dir / "database.py",
        module_dir / "clock.py",
        module_dir / "constants.py",
        module_dir / "money.py",
        module_dir / "importer.py",
        module_dir / "aggregate_validation.py",
        module_dir / "scd.py",
        module_dir / "service.py",
    ):
        digest.update(source.read_bytes())
    for source in sorted((module_dir / "sql").rglob("*.sql")):
        digest.update(str(source.relative_to(module_dir)).encode("utf-8"))
        digest.update(source.read_bytes())
    return digest.hexdigest()


def build_development_database(output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    database = Database(str(output))
    try:
        apply_migrations(database.connection)
    finally:
        database.close()

    service = DojoService(
        str(output),
        clock=FrozenClock(FIXTURE_TIME, business_date=date(2026, 10, 2)),
    )
    try:
        result = service.import_sheet_data(
            source="synthetic-development-fixture",
            source_kind="development_fixture",
            spreadsheet_title="Juniper Household Development Scenario",
            named_ranges=development_named_ranges(),
        )
        if not result["ok"]:
            raise RuntimeError("Development fixture failed aggregate validation")
        edit_target = service.db.fetch_one(
            """SELECT tx.transaction_id, tx.row_id, tx.date, tx.account_id, tx.amount_minor,
                      tx.category_id, tx.status
               FROM current_transactions AS tx
               JOIN current_categories AS category USING (category_id)
               WHERE category.name = 'Books' ORDER BY tx.date LIMIT 1"""
        )
        if edit_target is None:
            raise RuntimeError("Development fixture is missing its historical edit example")
        service.update_transaction(
            edit_target["transaction_id"],
            {
                "expected_version": edit_target["row_id"],
                "date": edit_target["date"],
                "account_id": edit_target["account_id"],
                "amount_minor": edit_target["amount_minor"],
                "category_id": edit_target["category_id"],
                "system_category": None,
                "status": edit_target["status"],
                "memo": "Papertrail Books purchase; memo corrected",
            },
        )
        with service.db.transaction() as connection:
            for category in connection.execute(
                """SELECT category_id, name, category_kind FROM current_categories
                   ORDER BY sort_order"""
            ).fetchall():
                category_id, name, category_kind = category
                goal_type = None
                if category_kind != CATEGORY_KIND_CREDIT_CARD_PAYMENT:
                    goal_type = (
                        "ONE_TIME"
                        if name in {"Annual Travel", "Home Project"}
                        else "DISCRETIONARY"
                        if name in {"Restaurants", "Hobbies", "Clothing"}
                        else "RECURRING"
                    )
                goal_amount = None
                if goal_type == "ONE_TIME":
                    goal_amount = {"Annual Travel": 150_000, "Home Project": 85_000}[name]
                elif goal_type == "RECURRING":
                    goal_amount = (
                        MONTHLY_PLANS.get(name, MERCHANTS.get(name, ("", 12_000))[1]) or 12_000
                    )
                connection.execute(
                    """UPDATE categories SET goal_type = ?, goal_amount_minor = ?,
                       goal_frequency = ?, goal_due_date = ?
                       WHERE category_id = ? AND valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00'""",
                    (
                        goal_type,
                        goal_amount,
                        "MONTHLY" if goal_type == "RECURRING" else None,
                        {"Annual Travel": "2026-12-31", "Home Project": "2026-10-31"}.get(name),
                        category_id,
                    ),
                )
            add_development_accounts(connection, FIXTURE_TIME)
    finally:
        service.close()
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic dojo development database"
    )
    parser.add_argument("output_path", help="DuckDB file to create or replace")
    args = parser.parse_args()
    output = build_development_database(args.output_path)
    print(
        json.dumps(
            {"path": str(output), "fingerprint": development_fixture_fingerprint()},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
