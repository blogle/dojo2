from __future__ import annotations

import json
from importlib import reload
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

import dojo.api.main as main_module
import dojo.api.routes as routes_module
from dojo.api.settings import get_settings
from dojo.migrations import provision_database


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
        response = client.post("/api/onboarding/google/start")
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
        start = client.post("/api/onboarding/google/start")
        assert start.status_code == 200
        auth_url = start.json()["auth_url"]
        assert isinstance(auth_url, str)
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
        delete_resp = client.delete(f"/api/transactions/{tx_id}")
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
