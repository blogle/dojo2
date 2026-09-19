from __future__ import annotations

import os
import secrets
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from dojo.backup_trigger import BackupTriggerError, trigger_backup

app = FastAPI(title="dojo backup trigger")
trigger_lock = Lock()


class TriggerRequest(BaseModel):
    run_id: str


def _authorize(authorization: Annotated[str | None, Header()] = None) -> None:
    token_file = Path(os.environ.get("BACKUP_TRIGGER_TOKEN_FILE", "/backup-status/token"))
    try:
        expected = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Backup trigger is not configured.") from exc
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or not expected
        or not secrets.compare_digest(authorization.removeprefix("Bearer "), expected)
    ):
        raise HTTPException(status_code=401, detail="Bearer token required")


@app.post("/trigger", status_code=202)
def trigger(
    payload: TriggerRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    _authorize(authorization)
    try:
        with trigger_lock:
            job_name = trigger_backup(
                api_url=os.environ["BACKUP_KUBERNETES_API_URL"],
                namespace=os.environ["BACKUP_KUBERNETES_NAMESPACE"],
                cronjob_name=os.environ.get("BACKUP_KUBERNETES_CRONJOB_NAME", "dojo-backup"),
                token_file=Path(os.environ["BACKUP_KUBERNETES_TOKEN_FILE"]),
                ca_file=Path(os.environ["BACKUP_KUBERNETES_CA_FILE"]),
                run_id=payload.run_id,
            )
    except (BackupTriggerError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Manual backup retry is unavailable.") from exc
    return {"status": "QUEUED", "job_name": job_name}
