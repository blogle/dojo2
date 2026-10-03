from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import dojo.dev_fixture as dev_fixture
from dojo.api.main import create_app
from dojo.api.settings import Settings
from dojo.clock import FrozenClock
from dojo.database import Database
from dojo.dev_fixture import build_development_database, development_fixture_fingerprint
from dojo.service import DojoService


def test_development_fixture_is_deterministic_and_financially_coherent(tmp_path) -> None:
    first_path = build_development_database(tmp_path / "first.duckdb")
    first_fingerprint = development_fixture_fingerprint()
    second_path = build_development_database(tmp_path / "second.duckdb")
    assert first_fingerprint == development_fixture_fingerprint()

    first = Database(str(first_path))
    second = Database(str(second_path))
    try:
        first_rows = first.fetch_all(
            """SELECT transaction_id, account_id, category_id, system_category, amount_minor,
                      date, status
               FROM current_transactions ORDER BY entry_order"""
        )
        second_rows = second.fetch_all(
            """SELECT transaction_id, account_id, category_id, system_category, amount_minor,
                      date, status
               FROM current_transactions ORDER BY entry_order"""
        )
        assert first_rows == second_rows
        assert first.fetch_all(
            "SELECT account_id, name, account_class FROM current_accounts ORDER BY name"
        ) == second.fetch_all(
            "SELECT account_id, name, account_class FROM current_accounts ORDER BY name"
        )
        assert first.fetch_all(
            """SELECT category_id, name, goal_type, goal_amount_minor
               FROM current_categories ORDER BY name"""
        ) == second.fetch_all(
            """SELECT category_id, name, goal_type, goal_amount_minor
               FROM current_categories ORDER BY name"""
        )
        assert first.fetch_all(
            """SELECT valuation_id, account_id, effective_date, amount_minor
               FROM current_net_worth_valuations ORDER BY effective_date, raw_name"""
        ) == second.fetch_all(
            """SELECT valuation_id, account_id, effective_date, amount_minor
               FROM current_net_worth_valuations ORDER BY effective_date, raw_name"""
        )
        assert 200 <= len(first_rows) < 1_000
        assert {row["date"].strftime("%Y-%m") for row in first_rows} == {
            "2026-01",
            "2026-02",
            "2026-03",
            "2026-04",
            "2026-05",
            "2026-06",
            "2026-07",
            "2026-08",
            "2026-09",
            "2026-10",
        }
        transfers = [
            row["amount_minor"] for row in first_rows if row["system_category"] == "TRANSFER"
        ]
        assert sum(transfers) == 0
        assert {row["status"] for row in first_rows} == {"CLEARED", "PENDING"}
        historical_edits = first.fetch_one(
            """SELECT COUNT(*) AS count FROM transactions
               WHERE valid_to <> TIMESTAMPTZ '9999-12-31 23:59:59+00'"""
        )
        assert historical_edits is not None and historical_edits["count"] >= 1

        categories = first.fetch_all("SELECT name, goal_type FROM current_categories")
        assert len(categories) >= 30
        assert {row["goal_type"] for row in categories} >= {
            "RECURRING",
            "ONE_TIME",
            "DISCRETIONARY",
        }
        assert len(first.fetch_all("SELECT * FROM current_category_groups")) >= 8
        assert {
            row["goal_frequency"]
            for row in first.fetch_all(
                "SELECT goal_frequency FROM current_categories WHERE goal_type = 'RECURRING'"
            )
        } >= {"MONTHLY", "YEARLY", "EVERY_6_MONTHS"}

        service = DojoService(
            str(first_path),
            clock=FrozenClock(datetime(2026, 10, 2, 12, tzinfo=timezone.utc), date(2026, 10, 2)),
        )
        try:
            for account in service.list_accounts(show_hidden=True):
                if account["account_class"] != "BUDGET":
                    continue
                ledger_total = first.fetch_one(
                    """SELECT COALESCE(SUM(amount_minor), 0) AS total
                       FROM current_transactions WHERE account_id = ?""",
                    (account["account_id"],),
                )
                assert ledger_total is not None
                assert account["actual_balance_minor"] == ledger_total["total"]
            assert service.get_app_status()["mode"] == "ready"
            account_classes = {
                row["account_class"] for row in service.list_accounts(show_hidden=True)
            }
            assert len(service.list_accounts(show_hidden=True)) == 9
            assert account_classes >= {
                "BUDGET",
                "TRACKING",
                "INVESTMENT",
                "LOAN",
                "TANGIBLE_ASSET",
            }
            current_categories = {
                row["name"]: row
                for row in service.list_categories(month="2026-10", show_hidden=True)
            }
            assert current_categories["Groceries"]["available_minor"] < 0
            assert current_categories["Rent"]["available_minor"] >= 0
            assert current_categories["Annual Travel"]["month_activity_minor"] == 0
            assert current_categories["Auto Loan Payment"]["goal_type"] == "RECURRING"
            assert current_categories["Auto Loan Payment"]["goal_amount_minor"] == 31_500
            assert current_categories["Auto Loan Payment"]["month_budgeted_minor"] == 0
            assert current_categories["Auto Loan Payment"]["goal_frequency"] == "MONTHLY"
            assert current_categories["Rent"]["goal_frequency"] == "MONTHLY"
            assert current_categories["Rent"]["goal_due_date"] == date(2026, 10, 5)
            assert current_categories["Rent"]["monthly_funding_minor"] == 145_000
            assert current_categories["Auto Loan Payment"]["goal_due_date"] == date(2026, 10, 15)
            assert current_categories["Auto Loan Payment"]["available_minor"] < 0
            assert current_categories["Insurance"]["goal_frequency"] == "YEARLY"
            assert current_categories["Insurance"]["goal_due_date"] == date(2027, 2, 15)
            assert current_categories["Insurance"]["monthly_funding_minor"] == 10_416
            assert current_categories["School"]["goal_frequency"] == "EVERY_6_MONTHS"
            assert current_categories["School"]["goal_due_date"] == date(2027, 2, 1)
            assert current_categories["School"]["monthly_funding_minor"] == 5_000

            annual_travel = current_categories["Annual Travel"]
            assert annual_travel["starting_available_minor"] > 0
            assert annual_travel["month_budgeted_minor"] > 0
            assert 0 < annual_travel["available_minor"] < annual_travel["goal_amount_minor"]
            assert annual_travel["monthly_funding_minor"] == 75_000
            home_project = current_categories["Home Project"]
            assert home_project["goal_type"] == "ONE_TIME"
            assert home_project["available_minor"] == 0
            assert home_project["goal_amount_minor"] == 85_000
            assert home_project["monthly_funding_minor"] == 85_000

            for category_name in ("Rent", "Annual Travel"):
                category = current_categories[category_name]
                assert category["available_minor"] == (
                    category["starting_available_minor"]
                    + category["month_budgeted_minor"]
                    + category["month_activity_minor"]
                )

            budget = service.get_budget("2026-10", show_hidden=True)
            atb = service.compute_available_to_budget()
            explanation = service.explain_available_to_budget(month="2026-10")
            assert budget["available_to_budget_minor"] == atb
            assert explanation["available_to_budget_minor"] == atb
            assert sum(component["amount_minor"] for component in explanation["components"]) == atb

            accounts_by_name = {
                account["name"]: account for account in service.list_accounts(show_hidden=True)
            }
            card_payment = current_categories["Cedar Card Payment"]
            card_account_id = accounts_by_name["Cedar Card"]["account_id"]
            assert card_payment["linked_account_id"] == card_account_id
            assert card_payment["available_minor"] > 0
            card_purchases = first.fetch_one(
                """SELECT COUNT(*) AS count, SUM(amount_minor) AS amount
                   FROM current_transactions
                   WHERE account_id = ? AND category_id IS NOT NULL""",
                (card_account_id,),
            )
            assert card_purchases is not None
            assert card_purchases["count"] > 0 and card_purchases["amount"] < 0
            payment_legs = first.fetch_all(
                """SELECT account.name, transaction.amount_minor
                   FROM current_transactions AS transaction
                   JOIN current_accounts AS account USING (account_id)
                   WHERE transaction.date = DATE '2026-06-25'
                     AND transaction.system_category = 'TX_ACCOUNT_TRANSFER'
                     AND transaction.memo IN ('Cedar card payment', 'Payment received')"""
            )
            assert {row["name"]: row["amount_minor"] for row in payment_legs} == {
                "Maple Checking": -25_000,
                "Cedar Card": 25_000,
            }

            unlinked_valuations = first.fetch_all(
                """SELECT valuation.account_id FROM current_net_worth_valuations AS valuation
                   JOIN current_accounts AS account USING (account_id)
                   WHERE account.account_class = 'BUDGET'"""
            )
            assert unlinked_valuations == []
        finally:
            service.close()

        app = create_app(Settings(DUCKDB_PATH=str(first_path), APP_ENV="development"))
        with TestClient(app) as client:
            bootstrap = client.get("/api/bootstrap")
            assert bootstrap.status_code == 200
            assert bootstrap.json()["app_status"]["mode"] == "ready"
    finally:
        first.close()
        second.close()


def test_failed_generation_preserves_existing_database(tmp_path, monkeypatch) -> None:
    target = tmp_path / "dev-fixture.duckdb"
    original = b"known-good fixture file"
    target.write_bytes(original)

    def fail_after_partial_build(path: Path) -> None:
        path.write_bytes(b"partial fixture")
        raise RuntimeError("synthetic fixture build failure")

    monkeypatch.setattr(dev_fixture, "_populate_development_database", fail_after_partial_build)

    with pytest.raises(RuntimeError, match="synthetic fixture build failure"):
        build_development_database(target)

    assert target.read_bytes() == original
    assert list(tmp_path.glob(".dev-fixture.duckdb.*.building")) == []
