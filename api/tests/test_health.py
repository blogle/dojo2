from __future__ import annotations

from importlib import reload

from fastapi.testclient import TestClient

import dojo.api.main as main_module
from dojo.api.settings import get_settings


def make_client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "health-test.duckdb"))
    monkeypatch.setenv("SESSION_SECRET", "health-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
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
