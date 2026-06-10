from fastapi.testclient import TestClient

from dojo.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "dojo"}


def test_api_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "dojo"}


def test_app_status() -> None:
    response = client.get("/api/app/status")

    assert response.status_code == 200
    assert response.json() == {"app": "dojo", "ready": False, "mode": "skeleton"}
