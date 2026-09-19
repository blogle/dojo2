from __future__ import annotations

import base64
from importlib import reload

from fastapi.testclient import TestClient

import dojo.api.internal_backup as internal_backup_module
import dojo.api.main as main_module
import dojo.api.routes as routes_module
from dojo.api.settings import get_settings
from dojo.backup_credentials import encrypt_refresh_token
from dojo.constants import SYSTEM_BACKUP_CREDENTIAL_ID
from dojo.drive_backup import GoogleAccessToken
from dojo.migrations import provision_database


def provisioned_client(monkeypatch, tmp_path) -> TestClient:
    database_path = tmp_path / "backup-access.duckdb"
    key_path = tmp_path / "credential-key"
    status_token_path = tmp_path / "status-token"
    key = b"0123456789abcdef0123456789abcdef"
    key_path.write_text(base64.b64encode(key).decode("ascii"), encoding="utf-8")
    status_token_path.write_text("internal-token", encoding="utf-8")
    monkeypatch.setenv("DUCKDB_PATH", str(database_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("BACKUP_STATUS_TOKEN_FILE", str(status_token_path))
    monkeypatch.setenv("DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE", str(key_path))
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    get_settings.cache_clear()
    provision_database(str(database_path))
    reload(main_module)
    return TestClient(main_module.app)


def configure_backup(client: TestClient, tmp_path) -> None:
    service = main_module.app.state.dojo_service
    key = b"0123456789abcdef0123456789abcdef"
    encrypted = encrypt_refresh_token(
        "opaque-refresh-value",
        credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
        key=key,
    )
    service.store_backup_credential(encrypted, "https://www.googleapis.com/auth/drive.file")
    service.start_empty_onboarding()
    service.configure_backup_folder("folder-id", "Backup folder", str(SYSTEM_BACKUP_CREDENTIAL_ID))


def test_backup_access_requires_internal_bearer_token(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        assert client.post("/api/internal/backup-access").status_code == 401
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer wrong-token"},
        )

    assert response.status_code == 403


def test_manual_backup_run_queues_a_job(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        configure_backup(client, tmp_path)
        main_module.app.state.dojo_service.report_backup_run(
            "00000000-0000-4000-8000-000000000001",
            {
                "trigger_kind": "SCHEDULED",
                "status": "FAILED",
                "phase": "SNAPSHOTTING",
                "error_message": "The snapshot did not become ready.",
            },
        )
        monkeypatch.setattr(
            routes_module,
            "request_backup_trigger",
            lambda **_kwargs: "dojo-backup-manual-abc",
        )

        response = client.post("/api/settings/backup/run")

    assert response.status_code == 202
    assert response.json() == {"status": "QUEUED", "job_name": "dojo-backup-manual-abc"}


def test_backup_access_rejects_missing_configuration(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer internal-token"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "backup_access_unavailable"


def test_backup_access_returns_only_short_lived_access(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        configure_backup(client, tmp_path)
        monkeypatch.setattr(
            internal_backup_module,
            "access_token_from_credential",
            lambda **_kwargs: GoogleAccessToken("short-lived-access", 3600),
        )
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer internal-token"},
        )

    assert response.status_code == 200
    assert set(response.json()) == {"access_token", "expires_in", "folder_id"}
    assert response.json() == {
        "access_token": "short-lived-access",
        "expires_in": 3600,
        "folder_id": "folder-id",
    }
    assert "opaque-refresh-value" not in response.text
    assert "client-secret" not in response.text


def test_backup_access_hides_invalid_credential_failures(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        service = main_module.app.state.dojo_service
        service.start_empty_onboarding()
        service.configure_backup_folder(
            "folder-id", "Backup folder", str(SYSTEM_BACKUP_CREDENTIAL_ID)
        )
        service.store_backup_credential("v1:invalid", "https://www.googleapis.com/auth/drive.file")
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer internal-token"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "backup_access_unavailable"
    assert "v1:invalid" not in response.text


def test_backup_access_rejects_configuration_linked_to_another_credential(
    monkeypatch, tmp_path
) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        service = main_module.app.state.dojo_service
        service.start_empty_onboarding()
        service.configure_backup_folder(
            "folder-id", "Backup folder", "00000000-0000-0000-0000-00000000ba03"
        )
        key = b"0123456789abcdef0123456789abcdef"
        service.store_backup_credential(
            encrypt_refresh_token(
                "opaque-refresh-value",
                credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
                key=key,
            ),
            "https://www.googleapis.com/auth/drive.file",
        )
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer internal-token"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "backup_access_unavailable"


def test_backup_access_rejects_credential_without_drive_scope(monkeypatch, tmp_path) -> None:
    with provisioned_client(monkeypatch, tmp_path) as client:
        service = main_module.app.state.dojo_service
        service.start_empty_onboarding()
        service.configure_backup_folder(
            "folder-id", "Backup folder", str(SYSTEM_BACKUP_CREDENTIAL_ID)
        )
        key = b"0123456789abcdef0123456789abcdef"
        service.store_backup_credential(
            encrypt_refresh_token(
                "opaque-refresh-value",
                credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
                key=key,
            ),
            "https://www.googleapis.com/auth/spreadsheets.readonly",
        )
        response = client.post(
            "/api/internal/backup-access",
            headers={"Authorization": "Bearer internal-token"},
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "backup_access_unavailable"


def test_new_onboarding_with_pending_backup_is_not_ready(service) -> None:
    status = service.start_empty_onboarding()

    assert status["ready"] is False
    assert status["mode"] == "backup_setup"
    assert status["backup"]["state"] == "required"


def test_existing_import_without_credential_remains_ready_and_degraded(imported_service) -> None:
    status = imported_service.get_app_status()

    assert status["ready"] is True
    assert status["mode"] == "ready"
    assert status["backup"]["state"] == "degraded"
    assert status["backup"]["action"] == "repair"


def test_configured_backup_without_run_is_ready_and_configured(service) -> None:
    key = b"0123456789abcdef0123456789abcdef"
    encrypted = encrypt_refresh_token(
        "opaque-refresh-value",
        credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
        key=key,
    )
    service.store_backup_credential(encrypted, "https://www.googleapis.com/auth/drive.file")
    service.start_empty_onboarding()
    service.configure_backup_folder("folder-id", "Backup folder", str(SYSTEM_BACKUP_CREDENTIAL_ID))

    status = service.get_app_status()

    assert status["ready"] is True
    assert status["mode"] == "ready"
    assert status["backup"]["state"] == "configured"
    assert status["backup"]["action"] == "repair"
    assert status["backup"]["message"] is None


def test_configured_backup_with_failed_run_remains_ready_and_degraded(service) -> None:
    key = b"0123456789abcdef0123456789abcdef"
    service.store_backup_credential(
        encrypt_refresh_token(
            "opaque-refresh-value",
            credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
            key=key,
        ),
        "https://www.googleapis.com/auth/drive.file",
    )
    service.start_empty_onboarding()
    service.configure_backup_folder("folder-id", "Backup folder", str(SYSTEM_BACKUP_CREDENTIAL_ID))
    service.report_backup_run(
        "00000000-0000-4000-8000-000000000001",
        {
            "trigger_kind": "SCHEDULED",
            "status": "FAILED",
            "phase": "SNAPSHOTTING",
            "error_message": "The snapshot did not become ready.",
        },
    )

    status = service.get_app_status()

    assert status["ready"] is True
    assert status["mode"] == "ready"
    assert status["backup"]["state"] == "degraded"
    assert status["backup"]["action"] == "retry"


def test_legacy_configured_folder_is_not_usable_after_backup_credential_repair(service) -> None:
    service.start_empty_onboarding()
    service.configure_backup_folder(
        "legacy-folder", "Legacy folder", str(SYSTEM_BACKUP_CREDENTIAL_ID)
    )
    service.db.execute(
        "UPDATE backup_configurations SET credential_id = NULL "
        "WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00'"
    )
    key = b"0123456789abcdef0123456789abcdef"
    service.store_backup_credential(
        encrypt_refresh_token(
            "opaque-refresh-value",
            credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
            key=key,
        ),
        "https://www.googleapis.com/auth/drive.file",
    )

    assert service.has_backup_credential() is True
    assert service.has_usable_backup_configuration() is False
    assert service.get_app_status()["backup"]["state"] == "degraded"


def test_backup_credential_without_drive_scope_is_not_authorized(service) -> None:
    key = b"0123456789abcdef0123456789abcdef"
    service.store_backup_credential(
        encrypt_refresh_token(
            "opaque-refresh-value",
            credential_id=SYSTEM_BACKUP_CREDENTIAL_ID,
            key=key,
        ),
        "https://www.googleapis.com/auth/spreadsheets.readonly",
    )

    assert service.has_backup_credential() is False
