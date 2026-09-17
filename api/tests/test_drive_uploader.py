from __future__ import annotations

import json
import subprocess
from pathlib import Path

import httpx
import pytest

from dojo.drive_uploader import (
    DriveUploadError,
    purge_repository,
    request_backup_access,
    restore_backup_snapshot,
    upload_backup,
)


def broker_response() -> httpx.Response:
    return httpx.Response(
        status_code=200,
        json={
            "access_token": "short-lived-access",
            "expires_in": 3600,
            "folder_id": "folder-id",
        },
        request=httpx.Request("POST", "http://dojo/api/internal/backup-access"),
    )


def test_request_backup_access_uses_internal_endpoint(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def post(url: str, **kwargs) -> httpx.Response:
        calls.append((url, kwargs["headers"]))
        return broker_response()

    monkeypatch.setattr("dojo.drive_uploader.httpx.post", post)

    payload = request_backup_access("http://dojo/", "internal-token")

    assert payload["folder_id"] == "folder-id"
    assert calls == [
        (
            "http://dojo/api/internal/backup-access",
            {"Authorization": "Bearer internal-token"},
        )
    ]


def test_request_backup_access_preserves_broker_failure_message(monkeypatch) -> None:
    response = httpx.Response(
        status_code=503,
        json={
            "detail": {
                "code": "google_drive_reauthorization_required",
                "message": "Google Drive authorization must be renewed.",
            }
        },
        request=httpx.Request("POST", "http://dojo/api/internal/backup-access"),
    )
    monkeypatch.setattr("dojo.drive_uploader.httpx.post", lambda *_args, **_kwargs: response)

    with pytest.raises(DriveUploadError, match="Google Drive authorization must be renewed"):
        request_backup_access("http://dojo", "internal-token")


def test_upload_creates_ephemeral_config_and_returns_snapshot_id(
    monkeypatch, tmp_path: Path
) -> None:
    staging = tmp_path / "stage"
    staging.mkdir()
    password = tmp_path / "password"
    password.write_text("restic-password", encoding="utf-8")
    observed_config: dict[str, str] = {}
    config_paths: list[Path] = []
    commands: list[list[str]] = []

    monkeypatch.setattr(
        "dojo.drive_uploader.httpx.post", lambda *_args, **_kwargs: broker_response()
    )

    def run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        config_path = Path(kwargs["env"]["RCLONE_CONFIG"])
        config_paths.append(config_path)
        observed_config["contents"] = config_path.read_text(encoding="utf-8")
        if command[1] == "snapshots":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        if command[1] == "backup":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({"message_type": "summary", "snapshot_id": "snapshot-id"}),
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("dojo.drive_uploader.subprocess.run", run)

    snapshot_id = upload_backup(
        staging,
        internal_api_url="http://dojo",
        internal_token="internal-token",
        restic_password_file=password,
        repository_path="dojo-rehearsals/test/restic",
        tags=("dojo",),
    )

    assert snapshot_id == "snapshot-id"
    assert commands[0][1] == "snapshots"
    assert commands[1][1] == "init"
    assert commands[2][1] == "backup"
    assert "root_folder_id = folder-id" in observed_config["contents"]
    assert "short-lived-access" in observed_config["contents"]
    assert "refresh_token" not in observed_config["contents"]
    assert "client_secret" not in observed_config["contents"]
    assert config_paths
    assert not config_paths[0].exists()


def test_upload_cleans_config_after_restic_failure(monkeypatch, tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    staging.mkdir()
    password = tmp_path / "password"
    password.write_text("restic-password", encoding="utf-8")
    config_paths: list[Path] = []
    monkeypatch.setattr(
        "dojo.drive_uploader.httpx.post", lambda *_args, **_kwargs: broker_response()
    )

    def run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        config_paths.append(Path(kwargs["env"]["RCLONE_CONFIG"]))
        if command[1] == "snapshots":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        if command[1] == "backup":
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("dojo.drive_uploader.subprocess.run", run)

    with pytest.raises(DriveUploadError, match="Restic command failed: backup"):
        upload_backup(
            staging,
            internal_api_url="http://dojo",
            internal_token="internal-token",
            restic_password_file=password,
            repository_path="dojo-rehearsals/test/restic",
        )

    assert config_paths
    assert not config_paths[0].exists()


def test_restore_uses_a_different_local_target(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "materialized"
    password = tmp_path / "password"
    password.write_text("restic-password", encoding="utf-8")
    commands: list[list[str]] = []
    monkeypatch.setattr(
        "dojo.drive_uploader.httpx.post", lambda *_args, **_kwargs: broker_response()
    )

    def run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("dojo.drive_uploader.subprocess.run", run)

    restore_backup_snapshot(
        "snapshot-id",
        target,
        internal_api_url="http://dojo",
        internal_token="internal-token",
        restic_password_file=password,
        repository_path="dojo-rehearsals/test/restic",
    )

    assert target.is_dir()
    assert commands == [["restic", "restore", "snapshot-id", "--target", str(target)]]


def test_purge_repository_rejects_production_repository(monkeypatch) -> None:
    with pytest.raises(DriveUploadError, match="Only a rehearsal repository"):
        purge_repository(
            "dojo/restic",
            internal_api_url="http://dojo",
            internal_token="internal-token",
        )


def test_purge_repository_cleans_ephemeral_config(monkeypatch) -> None:
    passwordless = broker_response()
    config_paths: list[Path] = []
    monkeypatch.setattr("dojo.drive_uploader.httpx.post", lambda *_args, **_kwargs: passwordless)

    def run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        config_paths.append(Path(kwargs["env"]["RCLONE_CONFIG"]))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("dojo.drive_uploader.subprocess.run", run)

    purge_repository(
        "dojo-rehearsals/test/restic",
        internal_api_url="http://dojo",
        internal_token="internal-token",
    )

    assert config_paths
    assert not config_paths[0].exists()
