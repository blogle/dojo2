from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

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
            assert current_categories["Auto Loan Payment"]["goal_amount_minor"] == 24_000
            assert current_categories["Auto Loan Payment"]["month_budgeted_minor"] == 0
            assert current_categories["Cedar Card Payment"]

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
