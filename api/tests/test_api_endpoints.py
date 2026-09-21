from __future__ import annotations

import base64
import json
from importlib import reload
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

import dojo.api.main as main_module
import dojo.api.routes as routes_module
from dojo.api.settings import get_settings
from dojo.drive_backup import GoogleAccessToken, VerifiedDriveFolder
from dojo.fixture_data import DEFAULT_FIXTURE
from dojo.migrations import provision_database
from dojo.sql import render_sql
from tests.support.scd_invariants import (
    assert_no_overlapping_versions,
    assert_single_current_version,
)


def provisioned_main_module(monkeypatch, tmp_path, filename: str):
    duckdb_path = tmp_path / filename
    monkeypatch.setenv("DUCKDB_PATH", str(duckdb_path))
    provision_database(str(duckdb_path))
    get_settings.cache_clear()
    reload(main_module)
    return main_module


def test_app_bootstrap_and_import_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        status = client.get("/api/app/status")
        assert status.status_code == 200
        assert status.json()["ready"] is False

        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200
        assert imported.json()["ok"] is True

        bootstrap = client.get("/api/bootstrap")
        assert bootstrap.status_code == 200
        assert bootstrap.json()["app_status"]["ready"] is True

        budget = client.get("/api/budget", params={"month": "2026-02", "show_hidden": "true"})
        assert budget.status_code == 200
        assert budget.json()["available_to_budget_minor"] == 424000
        assert budget.json()["groups"][0]["totals"]["available_minor"] == 26000

        breakdown = client.get(
            "/api/budget/available-to-budget-breakdown", params={"month": "2026-02"}
        )
        assert breakdown.status_code == 200
        breakdown_json = breakdown.json()
        assert breakdown_json["available_to_budget_minor"] == 424000
        assert breakdown_json["budget_month"] == "2026-02"
        assert breakdown_json["temporal_scope"] == "current-state"
        assert (
            sum(component["amount_minor"] for component in breakdown_json["components"]) == 424000
        )
        assert all("contributions" not in component for component in breakdown_json["components"])

        allocations = client.get(
            "/api/budget/available-to-budget-breakdown/allocations",
            params={"month": "2026-02"},
        )
        assert allocations.status_code == 200
        allocations_json = allocations.json()
        assert (
            sum(group["amount_minor"] for group in allocations_json["groups"])
            == (allocations_json["component"]["amount_minor"])
        )
        grocery = next(group for group in allocations_json["groups"] if group["label"] == "Grocery")

        records = client.get(
            "/api/budget/available-to-budget-breakdown/allocations/records",
            params={
                "month": "2026-02",
                "group_key": grocery["key"],
                "limit": 1,
            },
        )
        assert records.status_code == 200
        records_json = records.json()
        assert len(records_json["items"]) == 1
        assert records_json["items"][0]["category_name"] == "Grocery"
        assert records_json["limit"] == 1
        assert records_json["total"] == grocery["record_count"]

        transactions = client.get("/api/transactions", params={"show_hidden": "true", "limit": 100})
        assert transactions.status_code == 200
        assert len(transactions.json()["items"]) == 12


def test_budget_accounts_and_net_worth_endpoints_return_validated_aggregates(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200
        assert imported.json()["validation_report"]["passed"] is True

        budget_visible = client.get("/api/budget", params={"month": "2026-01"})
        assert budget_visible.status_code == 200
        assert budget_visible.json()["summary"]["spent_minor"] == 15000
        assert budget_visible.json()["groups"][0]["totals"]["month_budgeted_minor"] == 25000
        assert budget_visible.json()["groups"][0]["totals"]["starting_available_minor"] == 0

        budget_hidden = client.get(
            "/api/budget", params={"month": "2026-01", "show_hidden": "true"}
        )
        assert budget_hidden.status_code == 200
        assert budget_hidden.json()["summary"]["spent_minor"] == 19000

        accounts = client.get("/api/accounts", params={"show_hidden": "true"})
        assert accounts.status_code == 200
        reserve_card = next(
            account for account in accounts.json()["items"] if account["name"] == "Reserve Card"
        )
        assert reserve_card["actual_balance_minor"] == -20000
        assert reserve_card["display_balance_minor"] == 20000

        net_worth = client.get("/api/net-worth")
        assert net_worth.status_code == 200
        assert net_worth.json()["current_net_worth_minor"] == 49469000
        assert all(item.get("account_name") for item in net_worth.json()["items"])
        checking_ignored = next(
            item
            for item in net_worth.json()["items"]
            if item.get("account_name") == "Checking" and item.get("source") == "imported_valuation"
        )
        assert checking_ignored["ignored_import_value"] is True
        assert checking_ignored["ignored_reason"] == "duplicate_budget_account"

        assets_liabilities = client.get("/api/assets-liabilities")
        assert assets_liabilities.status_code == 200
        groups = {
            group["key"]: {item["name"] for item in group["items"]}
            for group in assets_liabilities.json()["groups"]
        }
        assert "House Value" in groups["TRACKING_ASSETS"]
        assert "House Value" not in groups["CASH"]
        assert "Car Loan" in groups["TRACKING_LIABILITIES"]
        assert "Car Loan" not in groups.get("LOANS", set())


def test_bootstrap_response_stays_shell_sized(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        bootstrap = client.get("/api/bootstrap")
        assert bootstrap.status_code == 200
        payload = bootstrap.json()
        payload_bytes = len(json.dumps(payload))

        assert sorted(payload.keys()) == ["app_status", "default_budget_month", "import_status"]
        assert payload_bytes < 20_000
        assert "validation_report" not in json.dumps(payload)


def test_transactions_endpoint_returns_bounded_sorted_pages(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        page = client.get(
            "/api/transactions",
            params={
                "show_hidden": "true",
                "limit": 5,
                "offset": 5,
                "sort_by": "date",
                "sort_dir": "desc",
            },
        )
        assert page.status_code == 200
        payload = page.json()

        assert len(payload["items"]) == 5
        assert payload["offset"] == 5
        assert payload["limit"] == 5
        assert payload["total"] == 12
        assert payload["has_more"] is True
        assert payload["items"][0]["date"] >= payload["items"][-1]["date"]


def test_transactions_endpoint_filters_by_account_with_status_counts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200
        accounts = client.get("/api/accounts", params={"show_hidden": "true"})
        checking = next(
            account for account in accounts.json()["items"] if account["name"] == "Checking"
        )

        page = client.get(
            "/api/transactions",
            params={
                "show_hidden": "true",
                "limit": 5,
                "account_id": checking["account_id"],
                "sort_by": "date",
                "sort_dir": "desc",
            },
        )
        assert page.status_code == 200
        payload = page.json()

        assert payload["total"] == 7
        assert payload["status_counts"] == {"PENDING": 1, "CLEARED": 6}
        assert payload["has_more"] is True
        assert {item["account_id"] for item in payload["items"]} == {checking["account_id"]}


def test_account_transaction_summary_is_aggregated_server_side(monkeypatch, tmp_path) -> None:
    import datetime
    from collections import defaultdict

    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200
        accounts = client.get("/api/accounts", params={"show_hidden": "true"})
        checking = next(
            account for account in accounts.json()["items"] if account["name"] == "Checking"
        )

        days = 365
        response = client.get(
            f"/api/accounts/{checking['account_id']}/transactions/summary",
            params={"days": days},
        )
        assert response.status_code == 200
        summary = response.json()

        assert summary["inflow_minor"] == 500_000
        assert summary["outflow_minor"] == -26_000
        assert summary["net_flow_minor"] == 474_000
        assert summary["transaction_count"] == 7

        # Reference: average daily balance over [today - days, today] using the
        # same anchored-daily-spine formula the SQL applies, so the server
        # output is verified against an independent computation.
        tx_page = client.get(
            "/api/transactions",
            params={"show_hidden": "true", "limit": 10_000, "account_id": checking["account_id"]},
        )
        amounts_by_day: dict[str, int] = defaultdict(int)
        for item in tx_page.json()["items"]:
            amounts_by_day[item["date"]] += item["amount_minor"]
        total_all = sum(amounts_by_day.values())
        display = checking["display_balance_minor"]
        today = datetime.datetime.now(datetime.timezone.utc).date()
        start = today - datetime.timedelta(days=days)
        balances: list[int] = []
        cum = 0
        day = start
        while day <= today:
            cum += amounts_by_day.get(day.isoformat(), 0)
            balances.append(display - total_all + cum)
            day += datetime.timedelta(days=1)
        expected_average = round(sum(balances) / len(balances))
        assert summary["average_daily_balance_minor"] == expected_average


def test_account_balance_trend_is_sampled_server_side(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200
        accounts = client.get("/api/accounts", params={"show_hidden": "true"})
        checking = next(
            account for account in accounts.json()["items"] if account["name"] == "Checking"
        )

        response = client.get(
            f"/api/accounts/{checking['account_id']}/balance-trend",
            params={"period": "all"},
        )
        assert response.status_code == 200
        points = response.json()["points"]

        assert len(points) == 2
        assert points[0]["date"] == "2026-01-01"
        assert points[0]["balance_minor"] == 381_000
        assert points[1]["date"] == "2026-02-01"
        assert points[1]["balance_minor"] == checking["display_balance_minor"]

        short = client.get(
            f"/api/accounts/{checking['account_id']}/balance-trend",
            params={"period": "1m"},
        )
        assert short.status_code == 200
        assert short.json()["points"] == []


def test_transactions_endpoint_rejects_unsupported_sort_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        response = client.get(
            "/api/transactions",
            params={"limit": 10, "sort_by": "memo", "sort_dir": "desc"},
        )
        assert response.status_code == 422


def test_google_start_endpoint_reports_fixture_mode_without_oauth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "")
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        response = client.post("/api/onboarding/google/start", json={"purpose": "aspire_migration"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["configured"] is False
        assert payload["fixture_mode"] is True
        assert payload["authorized"] is False


def test_google_import_requires_session_oauth_token(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        response = client.post("/api/import/google-sheet", json={"sheet_url_or_id": "sheet-123"})
        assert response.status_code == 400
        assert "Complete the OAuth step" in response.json()["detail"]


def test_google_callback_stores_token_in_memory_and_updates_status(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "exchange_google_code",
        lambda **_: {"access_token": "token-123", "token_type": "Bearer"},
    )

    with TestClient(main_module.app) as client:
        start = client.post("/api/onboarding/google/start", json={"purpose": "aspire_migration"})
        assert start.status_code == 200
        auth_url = start.json()["auth_url"]
        assert isinstance(auth_url, str)
        assert start.json()["callback_origin"] == "http://localhost:8000"
        state = parse_qs(urlparse(auth_url).query)["state"][0]

        callback = client.get(
            "/api/onboarding/google/callback",
            params={"code": "abc", "state": state},
        )
        assert callback.status_code == 200
        assert "dojo-google-oauth" in callback.text

        status = client.get("/api/onboarding/google/status")
        assert status.status_code == 200
        assert status.json()["authorized"] is True
        assert status.json()["backup_authorized"] is False
        assert status.json()["backup_reauthorization_required"] is True
        stored_token = next(
            iter(main_module.app.state.oauth_token_store._tokens_by_session_id.values())
        )
        assert stored_token["dojo_granted_scopes"] == (
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.file",
        )


def test_google_callback_defaults_missing_aspire_scopes_and_analyze_succeeds(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "exchange_google_code",
        lambda **_: {"access_token": "access-token", "token_type": "Bearer"},
    )
    monkeypatch.setattr(
        routes_module,
        "fetch_sheet_named_ranges",
        lambda **_: (
            "Aspire export",
            list(DEFAULT_FIXTURE["named_ranges"]),
            DEFAULT_FIXTURE["named_ranges"],
        ),
    )

    with TestClient(main_module.app) as client:
        start = client.post("/api/onboarding/google/start", json={"purpose": "aspire_migration"})
        assert start.status_code == 200
        state = parse_qs(urlparse(start.json()["auth_url"]).query)["state"][0]

        callback = client.get(
            "/api/onboarding/google/callback",
            params={"code": "abc", "state": state},
        )
        assert callback.status_code == 200

        stored_token = next(
            iter(main_module.app.state.oauth_token_store._tokens_by_session_id.values())
        )
        assert stored_token["dojo_granted_scopes"] == (
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.file",
        )

        analysis = client.post(
            "/api/import/google-sheet/analyze", json={"sheet_url_or_id": "sheet-123"}
        )
        assert analysis.status_code == 200
        assert analysis.json()["draft_id"]
        assert analysis.json()["review_items"]


def test_google_import_rejects_missing_sheets_grant_without_calling_sheets(
    monkeypatch, tmp_path
) -> None:
    key_path = tmp_path / "credential-key"
    key_path.write_text(
        base64.b64encode(b"0123456789abcdef0123456789abcdef").decode(), encoding="utf-8"
    )
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE", str(key_path))
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "exchange_google_code",
        lambda **_: {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "scope": "https://www.googleapis.com/auth/drive.file",
        },
    )

    def sheets_must_not_be_called(**_kwargs):
        raise AssertionError("Google Sheets must not be called without its granted scope")

    monkeypatch.setattr(routes_module, "fetch_sheet_named_ranges", sheets_must_not_be_called)

    with TestClient(main_module.app) as client:
        start = client.post("/api/onboarding/google/start", json={"purpose": "aspire_migration"})
        state = parse_qs(urlparse(start.json()["auth_url"]).query)["state"][0]
        assert (
            client.get(
                "/api/onboarding/google/callback", params={"code": "abc", "state": state}
            ).status_code
            == 200
        )
        assert client.get("/api/onboarding/google/status").json()["backup_authorized"] is True
        assert client.get("/api/onboarding/google/status").json()["authorized"] is False

        for path in ("/api/import/google-sheet", "/api/import/google-sheet/analyze"):
            response = client.post(path, json={"sheet_url_or_id": "sheet-123"})
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "google_sheets_authorization_required"
            assert "Connect Google again" in response.json()["detail"]["message"]


def test_google_callback_persists_refresh_token_encrypted(monkeypatch, tmp_path) -> None:
    key_path = tmp_path / "credential-key"
    key_path.write_text(
        base64.b64encode(b"0123456789abcdef0123456789abcdef").decode(), encoding="utf-8"
    )
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE", str(key_path))
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "exchange_google_code",
        lambda **_: {
            "access_token": "access-token",
            "refresh_token": "opaque-refresh-value",
            "scope": "https://www.googleapis.com/auth/drive.file",
        },
    )

    with TestClient(main_module.app) as client:
        start = client.post("/api/onboarding/google/start", json={"purpose": "backup"})
        state = parse_qs(urlparse(start.json()["auth_url"]).query)["state"][0]
        callback = client.get(
            "/api/onboarding/google/callback",
            params={"code": "abc", "state": state},
        )

        assert callback.status_code == 200
        assert "opaque-refresh-value" not in callback.text
        status = client.get("/api/onboarding/google/status")
        assert status.json()["backup_authorized"] is True
        assert "opaque-refresh-value" not in status.text
        credential = main_module.app.state.dojo_service.get_backup_credential()
        assert credential is not None
        assert credential["encrypted_refresh_token"].startswith("v1:")
        assert "opaque-refresh-value" not in str(credential)


def test_google_callback_completes_for_the_initiating_frontend_origin(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "exchange_google_code",
        lambda **_: {"access_token": "token-123", "token_type": "Bearer"},
    )

    with TestClient(main_module.app) as client:
        start = client.post(
            "/api/onboarding/google/start",
            json={"purpose": "aspire_migration"},
            headers={"Origin": "http://192.0.2.1:5173"},
        )
        state = parse_qs(urlparse(start.json()["auth_url"]).query)["state"][0]
        client.cookies.clear()

        callback = client.get(
            "/api/onboarding/google/callback",
            params={"code": "abc", "state": state},
        )

        assert callback.status_code == 200
        assert "http://192.0.2.1:5173" in callback.text


def test_delete_then_restore_preserves_transaction_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        # Get a transaction
        page = client.get(
            "/api/transactions",
            params={"show_hidden": "true", "limit": 1, "sort_by": "date", "sort_dir": "desc"},
        )
        assert page.status_code == 200
        tx = page.json()["items"][0]
        tx_id = tx["transaction_id"]

        # Delete it
        delete_resp = client.delete(
            f"/api/transactions/{tx_id}", params={"expected_version": tx["version"]}
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["ok"] is True

        # Verify deleted
        page_after_delete = client.get(
            "/api/transactions",
            params={"show_hidden": "true", "limit": 100, "sort_by": "date", "sort_dir": "desc"},
        )
        assert all(t["transaction_id"] != tx_id for t in page_after_delete.json()["items"])

        # Restore it
        restore_resp = client.post(f"/api/transactions/{tx_id}/restore")
        assert restore_resp.status_code == 200
        assert restore_resp.json()["transaction_id"] == tx_id

        # Verify restored with same ID
        page_after_restore = client.get(
            "/api/transactions",
            params={"show_hidden": "true", "limit": 100, "sort_by": "date", "sort_dir": "desc"},
        )
        restored_tx = next(
            t for t in page_after_restore.json()["items"] if t["transaction_id"] == tx_id
        )
        assert restored_tx["date"] == tx["date"]
        assert restored_tx["account_id"] == tx["account_id"]
        assert restored_tx["amount_minor"] == tx["amount_minor"]
        assert restored_tx["status"] == tx["status"]


def test_restore_missing_transaction_returns_404(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        # Try to restore a non-existent transaction (use valid UUID format)
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        restore_resp = client.post(f"/api/transactions/{non_existent_id}/restore")
        assert restore_resp.status_code == 404
        assert "Transaction not found" in restore_resp.json()["detail"]


def test_restore_already_active_transaction_returns_400(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        # Get a transaction
        page = client.get(
            "/api/transactions",
            params={"show_hidden": "true", "limit": 1, "sort_by": "date", "sort_dir": "desc"},
        )
        tx = page.json()["items"][0]
        tx_id = tx["transaction_id"]

        # Try to restore an already active transaction
        restore_resp = client.post(f"/api/transactions/{tx_id}/restore")
        assert restore_resp.status_code == 400
        assert "already active" in restore_resp.json()["detail"]


def test_import_results_in_entry_order_values_matching_source_order(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        page = client.get(
            "/api/transactions",
            params={
                "show_hidden": "true",
                "limit": 100,
                "sort_by": "entry_order",
                "sort_dir": "asc",
            },
        )
        assert page.status_code == 200
        items = page.json()["items"]
        assert len(items) == 12
        entry_orders = [item["entry_order"] for item in items]
        assert entry_orders == sorted(entry_orders)
        assert len(entry_orders) == len(set(entry_orders))


def test_same_date_transactions_maintain_entry_order(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        page = client.get(
            "/api/transactions",
            params={
                "show_hidden": "true",
                "limit": 100,
                "sort_by": "entry_order",
                "sort_dir": "asc",
            },
        )
        items = page.json()["items"]
        dates = [item["date"] for item in items]
        same_date_txs = [item for item in items if item["date"] == dates[0]]
        if len(same_date_txs) > 1:
            orders = [t["entry_order"] for t in same_date_txs]
            assert orders == sorted(orders)


def test_analyze_import_draft_returns_review_items(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        result = client.post(
            "/api/import/google-sheet/analyze",
            json={"sheet_url_or_id": "fixture://default"},
        )
        assert result.status_code == 200
        body = result.json()
        assert "draft_id" in body
        assert body["budget_account_count"] > 0
        assert body["net_worth_category_count"] > 0
        assert len(body["review_items"]) > 0

        item = body["review_items"][0]
        assert "raw_name" in item
        assert "latest_value_minor" in item
        assert "suggested_treatment" in item
        assert "confidence" in item
        assert item["confidence"] in ("HIGH", "MEDIUM", "LOW", "NONE")


def test_commit_import_draft_imports_data(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        analyze_result = client.post(
            "/api/import/google-sheet/analyze",
            json={"sheet_url_or_id": "fixture://default"},
        )
        draft_id = analyze_result.json()["draft_id"]
        review_items = analyze_result.json()["review_items"]

        decisions = []
        for item in review_items:
            decisions.append(
                {
                    "raw_name": item["raw_name"],
                    "treatment": "IMPORT_TRACKING_ACCOUNT",
                    "matched_account_id": None,
                    "polarity": item["suggested_polarity"],
                }
            )

        commit_result = client.post(
            "/api/import/google-sheet/commit",
            json={
                "draft_id": draft_id,
                "decisions": decisions,
                "low_confidence_confirmed": False,
            },
        )
        assert commit_result.status_code == 200
        commit_body = commit_result.json()
        assert commit_body["ok"] is True
        assert commit_body["validation_report"]["passed"] is True
        assert commit_body["decisions_summary"]["tracking_created"] > 0

        status = client.get("/api/app/status")
        assert status.status_code == 200
        assert status.json()["ready"] is False
        assert status.json()["mode"] == "backup_setup"


def test_transaction_update_rejects_stale_version(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        assert (
            client.post(
                "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
            ).status_code
            == 200
        )
        tx = client.get("/api/transactions", params={"show_hidden": "true", "limit": 1}).json()[
            "items"
        ][0]
        payload = {
            "date": tx["date"],
            "account_id": tx["account_id"],
            "amount_minor": tx["amount_minor"],
            "category_id": tx["category_id"],
            "system_category": tx["system_category"],
            "status": tx["status"],
            "memo": "first edit",
            "expected_version": tx["version"],
        }
        first = client.put(f"/api/transactions/{tx['transaction_id']}", json=payload)
        assert first.status_code == 200
        assert first.json()["version"] != tx["version"]

        stale = client.put(
            f"/api/transactions/{tx['transaction_id']}",
            json=payload | {"memo": "stale edit"},
        )
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "transaction_version_conflict"
        current = client.get(
            "/api/transactions", params={"show_hidden": "true", "limit": 100}
        ).json()["items"]
        updated = next(item for item in current if item["transaction_id"] == tx["transaction_id"])
        assert updated["memo"] == "first edit"


def test_transaction_update_preserves_scd_history_and_derived_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        imported = client.post(
            "/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"}
        )
        assert imported.status_code == 200

        transactions = client.get("/api/transactions", params={"show_hidden": "true", "limit": 100})
        assert transactions.status_code == 200
        transaction = next(
            item for item in transactions.json()["items"] if item["memo"] == "Groceries"
        )
        assert transaction["date"] == "2026-01-06"
        assert transaction["amount_minor"] == -5000
        assert transaction["status"] == "CLEARED"

        transaction_id = transaction["transaction_id"]
        original_version = transaction["version"]
        original_entry_order = transaction["entry_order"]
        service = main_module.app.state.dojo_service
        account_before = next(
            account
            for account in service.list_accounts(show_hidden=True)
            if str(account["account_id"]) == str(transaction["account_id"])
        )
        category_before = next(
            category
            for category in service.list_categories(month="2026-01", show_hidden=True)
            if str(category["category_id"]) == str(transaction["category_id"])
        )

        edit_payload = {
            "date": transaction["date"],
            "account_id": transaction["account_id"],
            "amount_minor": -5500,
            "category_id": transaction["category_id"],
            "system_category": transaction["system_category"],
            "status": transaction["status"],
            "memo": "Groceries adjusted",
            "expected_version": original_version,
        }
        edited = client.put(f"/api/transactions/{transaction_id}", json=edit_payload)
        assert edited.status_code == 200
        edited_body = edited.json()
        new_version = edited_body["version"]
        assert edited_body["transaction_id"] == transaction_id
        assert new_version != original_version

        history = service.db.fetch_all(
            render_sql(
                "templates/select_columns_where",
                columns="*",
                table="transactions",
                predicate="transaction_id = ?",
            ),
            (transaction_id,),
        )
        assert len(history) == 2
        original = next(row for row in history if str(row["row_id"]) == str(original_version))
        replacement = next(row for row in history if str(row["row_id"]) == str(new_version))
        assert all(str(row["transaction_id"]) == str(transaction_id) for row in history)
        assert original["valid_to"] != replacement["valid_to"]
        assert replacement["valid_to"] > replacement["valid_from"]
        assert original["entry_order"] == original_entry_order
        assert replacement["entry_order"] == original_entry_order
        assert original["amount_minor"] == -5000
        assert original["memo"] == "Groceries"
        assert replacement["amount_minor"] == -5500
        assert replacement["memo"] == "Groceries adjusted"
        current = assert_single_current_version(
            service.db, "transactions", "transaction_id", transaction_id
        )
        assert str(current["row_id"]) == str(new_version)
        assert_no_overlapping_versions(service.db, "transactions", "transaction_id", transaction_id)

        refetched = client.get("/api/transactions", params={"show_hidden": "true", "limit": 100})
        assert refetched.status_code == 200
        updated = next(
            item for item in refetched.json()["items"] if item["transaction_id"] == transaction_id
        )
        assert updated["transaction_id"] == transaction_id
        assert updated["version"] == new_version
        assert updated["entry_order"] == original_entry_order
        assert updated["amount_minor"] == -5500
        assert updated["memo"] == "Groceries adjusted"

        account_after = next(
            account
            for account in service.list_accounts(show_hidden=True)
            if str(account["account_id"]) == str(transaction["account_id"])
        )
        category_after = next(
            category
            for category in service.list_categories(month="2026-01", show_hidden=True)
            if str(category["category_id"]) == str(transaction["category_id"])
        )
        assert account_after["actual_balance_minor"] == account_before["actual_balance_minor"] - 500
        assert (
            category_after["month_activity_minor"] == category_before["month_activity_minor"] - 500
        )
        assert category_after["available_minor"] == category_before["available_minor"] - 500

        stale = client.put(
            f"/api/transactions/{transaction_id}",
            json=edit_payload | {"memo": "stale edit"},
        )
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "transaction_version_conflict"
        history_after_stale = service.db.fetch_all(
            render_sql(
                "templates/select_columns_where",
                columns="row_id",
                table="transactions",
                predicate="transaction_id = ?",
            ),
            (transaction_id,),
        )
        assert len(history_after_stale) == 2
        current_after_stale = assert_single_current_version(
            service.db, "transactions", "transaction_id", transaction_id
        )
        assert str(current_after_stale["row_id"]) == str(new_version)
        final = next(
            item
            for item in client.get(
                "/api/transactions", params={"show_hidden": "true", "limit": 100}
            ).json()["items"]
            if item["transaction_id"] == transaction_id
        )
        assert final["amount_minor"] == -5500
        assert final["memo"] == "Groceries adjusted"


def test_reviewed_import_requires_complete_decisions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")

    with TestClient(main_module.app) as client:
        analysis = client.post(
            "/api/import/google-sheet/analyze", json={"sheet_url_or_id": "fixture://default"}
        ).json()
        response = client.post(
            "/api/import/google-sheet/commit",
            json={
                "draft_id": analysis["draft_id"],
                "decisions": [],
                "low_confidence_confirmed": False,
            },
        )
        assert response.status_code == 400
        assert "missing" in response.json()["detail"]


def test_start_empty_requires_verified_backup_folder(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    monkeypatch.setattr(
        routes_module,
        "_get_backup_access_token",
        lambda _request: GoogleAccessToken("access-token", 3600),
    )
    monkeypatch.setattr(
        routes_module,
        "verify_drive_folder",
        lambda *_args, **_kwargs: VerifiedDriveFolder("canonical-folder", "Backup folder"),
    )

    with TestClient(main_module.app) as client:
        started = client.post("/api/onboarding/start-empty")
        assert started.status_code == 200
        assert started.json()["mode"] == "backup_setup"
        assert started.json()["ready"] is False

        settings = client.get("/api/settings/backup")
        assert settings.json()["google_drive_authorized"] is False
        assert settings.json()["reauthorization_required"] is True
        configured = client.put("/api/settings/backup", json={"folder_id": "drive-folder-123"})
        assert configured.status_code == 200
        assert configured.json()["configuration"]["status"] == "CONFIGURED"
        assert configured.json()["configuration"]["folder_name"] == "Backup folder"
        assert client.get("/api/app/status").json()["ready"] is True


def test_backup_status_endpoint_is_authenticated_and_non_blocking(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "backup-status-token"
    token_file.write_text("test-backup-token", encoding="utf-8")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("BACKUP_STATUS_TOKEN_FILE", str(token_file))
    provisioned_main_module(monkeypatch, tmp_path, "api-test.duckdb")
    run_id = "00000000-0000-4000-8000-000000000001"
    payload = {
        "trigger_kind": "SCHEDULED",
        "status": "FAILED",
        "phase": "UPLOADING",
        "error_message": "Drive access was revoked",
    }

    with TestClient(main_module.app) as client:
        assert client.post(f"/api/internal/backup-runs/{run_id}", json=payload).status_code == 401
        response = client.post(
            f"/api/internal/backup-runs/{run_id}",
            json=payload,
            headers={"Authorization": "Bearer test-backup-token"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "FAILED"
        assert client.get("/health").status_code == 200
