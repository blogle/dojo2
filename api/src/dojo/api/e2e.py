from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from dojo.e2e import (
    E2EScenario,
    activate_staged_baseline,
    baseline_path,
    fixed_e2e_clock,
    fixture_fingerprint,
    stage_baseline,
)
from dojo.google import OAuthTokenStore
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
        staged = stage_baseline(baseline, active_database)
        request.app.state.dojo_service.close()
        db_bytes = activate_staged_baseline(staged, active_database)
        restore_ms = (perf_counter() - started) * 1000

        started = perf_counter()
        request.app.state.dojo_service = DojoService(settings.duckdb_path, clock=fixed_e2e_clock())
        request.app.state.oauth_token_store = OAuthTokenStore()
        reopen_ms = (perf_counter() - started) * 1000

    return E2EResetResponse(
        scenario=payload.scenario,
        fixture_fingerprint=fixture_fingerprint(payload.scenario),
        fixed_time=fixed_e2e_clock().now().isoformat(),
        db_bytes=db_bytes,
        restore_ms=restore_ms,
        reopen_ms=reopen_ms,
    )
