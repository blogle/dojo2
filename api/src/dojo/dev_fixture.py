from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime, time, timezone
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from dojo.clock import FrozenClock
from dojo.database import Database
from dojo.dev_fixture_accounts import add_development_accounts
from dojo.dev_fixture_scenario import development_named_ranges
from dojo.migrations import apply_migrations
from dojo.service import DojoService

FIXTURE_TIME = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
CATEGORY_GOALS: dict[str, tuple[str, int, str | None, date | None]] = {
    "Rent": ("RECURRING", 145_000, "MONTHLY", date(2026, 10, 5)),
    "Electricity": ("RECURRING", 11_500, "MONTHLY", date(2026, 10, 20)),
    "Auto Loan Payment": ("RECURRING", 31_500, "MONTHLY", date(2026, 10, 15)),
    "Insurance": ("RECURRING", 125_000, "YEARLY", date(2027, 2, 15)),
    "School": ("RECURRING", 30_000, "EVERY_6_MONTHS", date(2027, 2, 1)),
    "Annual Travel": ("ONE_TIME", 150_000, None, date(2026, 12, 31)),
    "Home Project": ("ONE_TIME", 85_000, None, date(2026, 10, 31)),
    "Restaurants": ("DISCRETIONARY", 25_000, None, None),
    "Hobbies": ("DISCRETIONARY", 15_000, None, None),
    "Clothing": ("DISCRETIONARY", 20_000, None, None),
}


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
    temporary_output = output.with_name(f".{output.name}.{uuid4().hex}.building")
    try:
        _populate_development_database(temporary_output)
        _validate_development_database(temporary_output)
        os.replace(temporary_output, output)
    finally:
        temporary_output.unlink(missing_ok=True)
        Path(f"{temporary_output}.wal").unlink(missing_ok=True)
    return output


def _populate_development_database(output: Path) -> None:
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
            for category_id, name in connection.execute(
                "SELECT category_id, name FROM current_categories ORDER BY sort_order"
            ).fetchall():
                goal_type, goal_amount, goal_frequency, goal_due_date = CATEGORY_GOALS.get(
                    name, (None, None, None, None)
                )
                connection.execute(
                    """UPDATE categories SET goal_type = ?, goal_amount_minor = ?,
                       goal_frequency = ?, goal_due_date = ?
                       WHERE category_id = ? AND valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00'""",
                    (
                        goal_type,
                        goal_amount,
                        goal_frequency,
                        goal_due_date,
                        category_id,
                    ),
                )
            add_development_accounts(connection, FIXTURE_TIME)
        _add_development_investment_positions(service)
        _add_development_reconciliation_history(service)
    finally:
        service.close()


def _add_development_reconciliation_history(service: DojoService) -> None:
    accounts_by_name = {
        str(account["name"]): account for account in service.list_accounts(show_hidden=True)
    }
    checking = accounts_by_name["Maple Checking"]
    attempt = service.create_reconciliation_draft(
        str(checking["account_id"]),
        {
            "source_kind": "BANK_STATEMENT",
            "cutoff": service.clock.today(),
            "source_cleared_minor": checking["cleared_balance_minor"],
            "source_pending_minor": checking["pending_balance_minor"],
            "source_as_of": FIXTURE_TIME,
        },
    )
    if not attempt["certification_allowed"]:
        raise RuntimeError("Development budget reconciliation does not match its ledger")
    service.apply_reconciliation(
        str(attempt["reconciliation_id"]), {"client_operation_id": str(uuid4())}
    )

    investment = accounts_by_name["Pinecone Brokerage"]
    statement = service.latest_investment_statement(str(investment["account_id"]))
    position_values = [
        {
            "instrument_id": position["instrument_id"],
            "quantity_micros": position["quantity_micros"],
            "total_cost_basis_minor": position["total_cost_basis_minor"],
            "source_price_minor": position["price_minor"],
            "source_value_minor": position["value_minor"],
        }
        for position in statement["holdings"]
    ]
    investment_attempt = service.create_reconciliation_draft(
        str(investment["account_id"]),
        {
            "source_kind": "INVESTMENT_STATEMENT",
            "cutoff": date.fromisoformat(str(statement["effective_date"])),
            "source_as_of": datetime.combine(
                date.fromisoformat(str(statement["effective_date"])), time(12), timezone.utc
            ),
            "source_cash_minor": statement["cash_balance_minor"],
            "source_total_value_minor": statement["cash_balance_minor"]
            + sum(position["source_value_minor"] for position in position_values),
            "source_positions": position_values,
        },
    )
    if not investment_attempt["certification_allowed"]:
        raise RuntimeError("Development investment reconciliation does not match its holdings")
    service.apply_reconciliation(
        str(investment_attempt["reconciliation_id"]),
        {"client_operation_id": str(uuid4())},
    )

    loan = accounts_by_name["Cedar Auto Loan"]
    snapshot = service.list_loan_snapshots(str(loan["account_id"]))[0]
    loan_facts = {
        field: snapshot[field]
        for field in (
            "principal_balance_minor",
            "accrued_interest_minor",
            "escrow_balance_minor",
            "unapplied_credit_minor",
            "ytd_principal_paid_minor",
            "ytd_interest_paid_minor",
        )
        if snapshot[field] is not None
    }
    service.reconcile_loan(
        str(loan["account_id"]),
        {
            "source_as_of": datetime.combine(snapshot["effective_date"], time(12), timezone.utc),
            **loan_facts,
        },
    )

    for name in ("Harbor Education Fund", "Juniper Home"):
        account = accounts_by_name[name]
        service.reconcile_valuation(
            str(account["account_id"]),
            {
                "effective_date": date.fromisoformat(str(account["value_effective_date"])),
                "amount_minor": account["current_value_minor"],
                "source": "manual",
                "notes": "Fictional development-fixture source",
                "client_operation_id": str(uuid4()),
            },
        )


def _add_development_investment_positions(service: DojoService) -> None:
    account = next(
        account
        for account in service.list_accounts(show_hidden=True)
        if account["name"] == "Pinecone Brokerage"
    )
    instruments = {
        str(instrument["symbol"]): str(instrument["instrument_id"])
        for instrument in service.list_investment_instruments()
    }
    statement = service.latest_investment_statement(str(account["account_id"]))
    service.reconcile_investment_statement(
        str(account["account_id"]),
        {
            "effective_date": date.fromisoformat(str(statement["effective_date"])),
            "cash_balance_minor": statement["cash_balance_minor"],
            "notes": "Fictional development-fixture statement",
            "holdings": [
                {
                    "instrument_id": instruments["CASH"],
                    "quantity_micros": 25_000_000,
                    "price_minor": 5_000,
                    "total_cost_basis_minor": 110_000,
                },
                {
                    "instrument_id": instruments["IDX"],
                    "quantity_micros": 10_000_000,
                    "price_minor": 10_000,
                    "total_cost_basis_minor": 90_000,
                },
            ],
        },
    )


def _validate_development_database(path: Path) -> None:
    service = DojoService(
        str(path),
        clock=FrozenClock(FIXTURE_TIME, business_date=date(2026, 10, 2)),
    )
    try:
        if service.get_app_status()["mode"] != "ready":
            raise RuntimeError("Development fixture did not enter the ready application state")
        transaction_count = service.db.fetch_one(
            "SELECT COUNT(*) AS count FROM current_transactions"
        )
        if transaction_count is None or not 200 <= transaction_count["count"] < 1_000:
            raise RuntimeError("Development fixture has an unexpected transaction count")
        invalid_transaction_categories = service.db.fetch_one(
            "SELECT COUNT(*) AS count FROM transactions "
            "WHERE (category_id IS NULL) = (system_category IS NULL)"
        )
        if invalid_transaction_categories is None or invalid_transaction_categories["count"]:
            raise RuntimeError(
                "Development fixture contains transactions without one category target"
            )
        required_frequencies = {"MONTHLY", "YEARLY", "EVERY_6_MONTHS"}
        configured_frequencies = {
            category["goal_frequency"]
            for category in service.list_categories(month="2026-10", show_hidden=True)
            if category["goal_type"] == "RECURRING"
        }
        if not required_frequencies <= configured_frequencies:
            raise RuntimeError("Development fixture is missing recurring goal frequencies")
    finally:
        service.close()


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
