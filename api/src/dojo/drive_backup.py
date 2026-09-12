from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx


def _refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> str:
    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def build_rclone_config(
    *,
    folder_id: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> str:
    access_token = _refresh_access_token(client_id, client_secret, refresh_token)
    token_payload = json.dumps({
        "access_token": access_token,
        "token_type": "Bearer",
        "refresh_token": refresh_token,
        "expiry": "2000-01-01T00:00:00Z",
    })
    return (
        f"[gdrive]\n"
        f"type = drive\n"
        f"scope = drive\n"
        f"client_id = {client_id}\n"
        f"client_secret = {client_secret}\n"
        f"token = {token_payload}\n"
        f"root_folder_id = {folder_id}\n"
    )


def verify_drive_folder(
    folder_id: str,
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> None:
    config_content = build_rclone_config(
        folder_id=folder_id,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(config_content)
        config_path = f.name

    try:
        remote = f":drive,scope=drive,root_folder_id={folder_id}:"
        environment = os.environ | {"RCLONE_CONFIG": config_path}
        probe = f".dojo-access-probe-{uuid4()}"
        try:
            subprocess.run(
                ["rclone", "lsf", remote, "--max-depth", "1"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
            )
            subprocess.run(
                ["rclone", "mkdir", f"{remote}{probe}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
            )
            subprocess.run(
                ["rclone", "rcat", f"{remote}{probe}/storage-check"],
                input=b"ok",
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
            )
            subprocess.run(
                ["rclone", "delete", f"{remote}{probe}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
            )
            subprocess.run(
                ["rclone", "rmdir", f"{remote}{probe}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=environment,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError(
                "dojo could not write to that Google Drive folder. "
                "Confirm the folder ID and that you granted Drive access during sign-in."
            ) from exc
    finally:
        Path(config_path).unlink(missing_ok=True)
