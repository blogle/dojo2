from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from dojo.e2e import (
    E2EGoogleSheetsStub,
    E2EScenario,
    activate_staged_baseline,
    baseline_path,
    fixed_e2e_clock,
    fixture_fingerprint,
    stage_baseline,
)
from dojo.google import DOJO_GRANTED_SCOPES_KEY, OAuthTokenStore
from dojo.service import DojoService

router = APIRouter(prefix="/__e2e", tags=["e2e"])


class E2EResetRequest(BaseModel):
    scenario: E2EScenario


class E2EResetResponse(BaseModel):
    scenario: E2EScenario
    fixture_fingerprint: str
    fixed_time: str
    db_bytes: int
    restore_ms: float
    reopen_ms: float


class E2EGoogleGrantRequest(BaseModel):
    scopes: list[str]


class E2EGoogleSheetsRequest(BaseModel):
    spreadsheet_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/reset", response_model=E2EResetResponse)
async def reset(
    request: Request,
    payload: E2EResetRequest,
    x_dojo_e2e_token: str | None = Header(default=None),
) -> E2EResetResponse:
    settings = request.app.state.settings
    expected = settings.e2e_reset_token
    if not expected or x_dojo_e2e_token is None or x_dojo_e2e_token != expected:
        raise HTTPException(status_code=403, detail="Invalid E2E reset token")

    run_dir = Path(settings.e2e_run_dir).resolve()
    active_database = Path(settings.duckdb_path).resolve()
    sentinel = run_dir / ".dojo-e2e-worker"
    if (
        active_database != run_dir / "worker.duckdb"
        or not sentinel.is_file()
        or sentinel.read_text(encoding="utf-8") != expected
    ):
        raise HTTPException(status_code=409, detail="Unsafe E2E worker database configuration")

    baseline = baseline_path(settings.e2e_baseline_dir, payload.scenario)
    if not baseline.exists():
        raise HTTPException(status_code=409, detail="E2E baseline has not been generated")

    async with request.app.state.e2e_reset_lock:
        started = perf_counter()
        replacement_database = run_dir / f"worker-{uuid4()}.duckdb"
        staged = stage_baseline(baseline, replacement_database)
        db_bytes = activate_staged_baseline(staged, replacement_database)
        restore_ms = (perf_counter() - started) * 1000

        started = perf_counter()
        try:
            replacement_service = DojoService(str(replacement_database), clock=fixed_e2e_clock())
        except Exception:
            replacement_database.unlink(missing_ok=True)
            raise
        previous_service = request.app.state.dojo_service
        previous_database = request.app.state.e2e_active_database
        request.app.state.dojo_service = replacement_service
        request.app.state.e2e_active_database = replacement_database
        request.app.state.oauth_token_store = OAuthTokenStore()
        request.app.state.e2e_google_sheets = None
        previous_service.close()
        if previous_database.parent == run_dir:
            previous_database.unlink(missing_ok=True)
        reopen_ms = (perf_counter() - started) * 1000

    return E2EResetResponse(
        scenario=payload.scenario,
        fixture_fingerprint=fixture_fingerprint(payload.scenario),
        fixed_time=fixed_e2e_clock().now().isoformat(),
        db_bytes=db_bytes,
        restore_ms=restore_ms,
        reopen_ms=reopen_ms,
    )


@router.post("/google-sheets")
def configure_google_sheets_stub(
    request: Request, payload: E2EGoogleSheetsRequest
) -> dict[str, Any]:
    request.app.state.e2e_google_sheets = E2EGoogleSheetsStub(payload.spreadsheet_id)
    return google_sheets_stub_status(request)


@router.get("/google-sheets")
def google_sheets_stub_status(request: Request) -> dict[str, Any]:
    stub = request.app.state.e2e_google_sheets
    if not isinstance(stub, E2EGoogleSheetsStub):
        raise HTTPException(status_code=409, detail="E2E Google Sheets stub is not configured")
    return {
        "spreadsheet_id": stub.spreadsheet_id,
        "call_count": stub.call_count,
        "requested_spreadsheet_ids": stub.requested_spreadsheet_ids,
    }


@router.post("/google-session")
async def set_google_session(
    request: Request, payload: E2EGoogleGrantRequest
) -> dict[str, list[str]]:
    session_id = request.session.get("google_oauth_session_id")
    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(status_code=409, detail="Google OAuth session has not been initialized")
    request.app.state.oauth_token_store.set(
        session_id,
        {
            "access_token": "e2e-google-access-token",
            DOJO_GRANTED_SCOPES_KEY: tuple(sorted(set(payload.scopes))),
        },
    )
    return {"scopes": payload.scopes}
