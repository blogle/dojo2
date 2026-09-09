from __future__ import annotations

import secrets
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

from dojo.api.models import BackupRunEventPayload
from dojo.api.settings import Settings
from dojo.service import DojoService

router = APIRouter(prefix="/api/internal/backup-runs")


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


@router.post("/{run_id}")
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
