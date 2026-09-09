from __future__ import annotations

import os
import subprocess
from pathlib import Path
from uuid import uuid4


def verify_drive_folder(folder_id: str, service_account_file: str) -> None:
    credential_path = Path(service_account_file)
    if not service_account_file or not credential_path.is_file():
        raise RuntimeError("Backup service account credentials are not configured")

    remote = (
        f":drive,scope=drive,service_account_file={credential_path},root_folder_id={folder_id}:"
    )
    environment = os.environ | {"RCLONE_CONFIG": os.devnull}
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
            ["rclone", "rmdir", f"{remote}{probe}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(
            "dojo could not write to that Google Drive folder. Confirm the folder ID and sharing permissions."
        ) from exc
