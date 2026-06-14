from __future__ import annotations

from importlib import reload

from fastapi.testclient import TestClient

import dojo.api.main as main_module
from dojo.api.settings import get_settings
from dojo.migrations import provision_database


def make_client(monkeypatch, tmp_path) -> TestClient:
    duckdb_path = tmp_path / "health-test.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(duckdb_path))
    monkeypatch.setenv("SESSION_SECRET", "health-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    provision_database(str(duckdb_path))
    get_settings.cache_clear()
    reload(main_module)
    return TestClient(main_module.app)


def test_health(monkeypatch, tmp_path) -> None:
    with make_client(monkeypatch, tmp_path) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "dojo"}


def test_api_health(monkeypatch, tmp_path) -> None:
    with make_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "dojo"}


def test_app_status(monkeypatch, tmp_path) -> None:
    with make_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/app/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "dojo"
    assert payload["ready"] is False
    assert payload["mode"] == "onboarding"
