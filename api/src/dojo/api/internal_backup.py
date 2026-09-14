from __future__ import annotations

import secrets
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

from dojo.api.models import BackupRunEventPayload
from dojo.api.settings import Settings
from dojo.drive_backup import (
    GoogleDriveAuthorizationError,
    GoogleDriveError,
    access_token_from_credential,
)
from dojo.service import DojoService

router = APIRouter(prefix="/api/internal")


def _authorize(request: Request, authorization: Annotated[str | None, Header()] = None) -> None:
    settings = cast(Settings, request.app.state.settings)
    if not settings.backup_status_token_file:
        raise HTTPException(status_code=503, detail="Backup status reporting is not configured")
    try:
        expected = Path(settings.backup_status_token_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(
            status_code=503, detail="Backup status reporting is not configured"
        ) from exc
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not expected or not secrets.compare_digest(authorization.removeprefix("Bearer "), expected):
        raise HTTPException(status_code=403, detail="Invalid backup status token")


@router.post("/backup-runs/{run_id}")
def report_backup_run(
    request: Request,
    run_id: UUID,
    payload: BackupRunEventPayload,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _authorize(request, authorization)
    service = cast(DojoService, request.app.state.dojo_service)
    try:
        return service.report_backup_run(str(run_id), payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/backup-access")
def backup_access(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _authorize(request, authorization)
    settings = cast(Settings, request.app.state.settings)
    service = cast(DojoService, request.app.state.dojo_service)
    configuration = service.get_backup_configuration()
    credential = service.get_backup_credential()
    if not service.has_usable_backup_configuration() or configuration is None or credential is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "backup_access_unavailable",
                "message": "A configured encrypted Google Drive credential is required.",
            },
        )
    try:
        access_token = access_token_from_credential(
            encrypted_refresh_token=str(credential["encrypted_refresh_token"]),
            credential_id=str(credential["credential_id"]),
            encryption_key_file=settings.credential_encryption_key_file,
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
        )
    except GoogleDriveAuthorizationError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "google_drive_reauthorization_required",
                "message": "Google Drive authorization must be renewed.",
            },
        ) from exc
    except (GoogleDriveError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "backup_access_unavailable",
                "message": "A usable Google Drive access token could not be obtained.",
            },
        ) from exc
    return {
        "access_token": access_token.access_token,
        "expires_in": access_token.expires_in,
        "folder_id": configuration["drive_folder_id"],
    }
