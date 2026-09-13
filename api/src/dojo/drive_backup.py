from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from uuid import uuid4

import httpx

from dojo.backup_credentials import decrypt_refresh_token, load_encryption_key

GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class GoogleDriveAuthorizationError(RuntimeError):
    """Raised when Google rejects the durable Drive authorization."""


class GoogleDriveError(RuntimeError):
    """Raised when a Drive operation cannot be completed safely."""


@dataclass(frozen=True)
class GoogleAccessToken:
    access_token: str
    expires_in: int


@dataclass(frozen=True)
class VerifiedDriveFolder:
    folder_id: str
    folder_name: str


def refresh_google_access_token(
    *, client_id: str, client_secret: str, refresh_token: str
) -> GoogleAccessToken:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    if response.status_code in {400, 401, 403}:
        raise GoogleDriveAuthorizationError("Google Drive authorization must be renewed.")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise GoogleDriveError("Google Drive authorization could not be refreshed.") from exc
    payload = cast(dict[str, Any], response.json())
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise GoogleDriveError("Google did not return a usable Drive access token.")
    expires_in = payload.get("expires_in", 3600)
    if not isinstance(expires_in, int):
        raise GoogleDriveError("Google returned an invalid Drive token lifetime.")
    return GoogleAccessToken(access_token=access_token, expires_in=expires_in)


def access_token_from_credential(
    *,
    encrypted_refresh_token: str,
    credential_id: str,
    encryption_key_file: str,
    client_id: str,
    client_secret: str,
) -> GoogleAccessToken:
    key = load_encryption_key(encryption_key_file)
    refresh_token = decrypt_refresh_token(
        encrypted_refresh_token,
        credential_id=credential_id,
        key=key,
    )
    return refresh_google_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )


def verify_drive_folder(folder_id: str, *, access_token: str) -> VerifiedDriveFolder:
    headers = {"Authorization": f"Bearer {access_token}"}
    metadata_response = httpx.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{folder_id}",
        params={
            "fields": "id,name,mimeType",
            "supportsAllDrives": "true",
        },
        headers=headers,
        timeout=30.0,
    )
    _raise_drive_response(metadata_response)
    metadata = cast(dict[str, Any], metadata_response.json())
    if metadata.get("mimeType") != GOOGLE_FOLDER_MIME_TYPE:
        raise GoogleDriveError("The selected Google Drive item is not a folder.")
    canonical_id = metadata.get("id")
    canonical_name = metadata.get("name")
    if not isinstance(canonical_id, str) or not isinstance(canonical_name, str):
        raise GoogleDriveError("Google did not return complete folder metadata.")

    probe_id: str | None = None
    try:
        probe_response = httpx.post(
            GOOGLE_DRIVE_FILES_URL,
            params={"supportsAllDrives": "true"},
            headers=headers,
            json={
                "name": f".dojo-access-probe-{uuid4()}",
                "parents": [canonical_id],
                "mimeType": "application/octet-stream",
            },
            timeout=30.0,
        )
        _raise_drive_response(probe_response)
        probe = cast(dict[str, Any], probe_response.json())
        probe_id = probe.get("id")
        if not isinstance(probe_id, str) or not probe_id:
            raise GoogleDriveError("Google did not return the access probe ID.")
    finally:
        if probe_id is not None:
            cleanup_response = httpx.delete(
                f"{GOOGLE_DRIVE_FILES_URL}/{probe_id}",
                params={"supportsAllDrives": "true"},
                headers=headers,
                timeout=30.0,
            )
            _raise_drive_response(cleanup_response)

    return VerifiedDriveFolder(folder_id=canonical_id, folder_name=canonical_name)


def _raise_drive_response(response: httpx.Response) -> None:
    if response.status_code in {401, 403}:
        raise GoogleDriveAuthorizationError("Google Drive authorization must be renewed.")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise GoogleDriveError("Google Drive operation failed.") from exc
