from __future__ import annotations

from typing import Any

import httpx
import pytest

from dojo.drive_backup import (
    GOOGLE_FOLDER_MIME_TYPE,
    GoogleDriveAuthorizationError,
    GoogleDriveError,
    GoogleDrivePermissionError,
    verify_drive_folder,
)


def response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=payload,
        request=httpx.Request("GET", "https://example.com"),
    )


def test_verify_drive_folder_fetches_metadata_and_cleans_probe(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def get(url: str, **_kwargs) -> httpx.Response:
        calls.append(("GET", url))
        return response(
            200,
            {
                "id": "canonical-folder",
                "name": "Backup folder",
                "mimeType": GOOGLE_FOLDER_MIME_TYPE,
            },
        )

    def post(url: str, **_kwargs) -> httpx.Response:
        calls.append(("POST", url))
        return response(200, {"id": "probe-id"})

    def delete(url: str, **_kwargs) -> httpx.Response:
        calls.append(("DELETE", url))
        return response(204, {})

    monkeypatch.setattr("dojo.drive_backup.httpx.get", get)
    monkeypatch.setattr("dojo.drive_backup.httpx.post", post)
    monkeypatch.setattr("dojo.drive_backup.httpx.delete", delete)

    folder = verify_drive_folder("selected-folder", access_token="access-token")

    assert folder.folder_id == "canonical-folder"
    assert folder.folder_name == "Backup folder"
    assert [method for method, _url in calls] == ["GET", "POST", "DELETE"]
    assert calls[-1][1].endswith("/probe-id")


def test_verify_drive_folder_rejects_non_folder(monkeypatch) -> None:
    monkeypatch.setattr(
        "dojo.drive_backup.httpx.get",
        lambda *_args, **_kwargs: response(
            200,
            {"id": "file-id", "name": "Not a folder", "mimeType": "text/plain"},
        ),
    )

    with pytest.raises(GoogleDriveError, match="not a folder"):
        verify_drive_folder("selected-file", access_token="access-token")


def test_verify_drive_folder_attempts_cleanup_when_probe_delete_fails(monkeypatch) -> None:
    deleted = False

    monkeypatch.setattr(
        "dojo.drive_backup.httpx.get",
        lambda *_args, **_kwargs: response(
            200,
            {"id": "folder-id", "name": "Backup folder", "mimeType": GOOGLE_FOLDER_MIME_TYPE},
        ),
    )
    monkeypatch.setattr(
        "dojo.drive_backup.httpx.post",
        lambda *_args, **_kwargs: response(200, {"id": "probe-id"}),
    )

    def delete(*_args, **_kwargs) -> httpx.Response:
        nonlocal deleted
        deleted = True
        return response(403, {"error": {"errors": [{"reason": "insufficientFilePermissions"}]}})

    monkeypatch.setattr("dojo.drive_backup.httpx.delete", delete)

    with pytest.raises(GoogleDrivePermissionError):
        verify_drive_folder("folder-id", access_token="access-token")
    assert deleted is True


def test_drive_unauthorized_and_unrecognized_forbidden_are_distinct() -> None:
    from dojo.drive_backup import _raise_drive_response

    with pytest.raises(GoogleDriveAuthorizationError):
        _raise_drive_response(response(401, {}))
    with pytest.raises(GoogleDriveError):
        _raise_drive_response(
            response(403, {"error": {"errors": [{"reason": "rateLimitExceeded"}]}})
        )
