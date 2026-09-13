from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import httpx


class DriveUploadError(RuntimeError):
    """Raised when the platform-neutral Drive upload cannot complete."""


def upload_backup(
    staging_directory: Path,
    *,
    internal_api_url: str,
    internal_token: str,
    restic_password_file: Path,
    repository_path: str,
    tags: tuple[str, ...] = (),
    retain: bool = False,
) -> str:
    access = request_backup_access(internal_api_url, internal_token)
    config_path = _write_rclone_config(access["access_token"], access["folder_id"])
    try:
        environment = os.environ | {
            "RCLONE_CONFIG": str(config_path),
            "RESTIC_REPOSITORY": f"rclone:gdrive:{repository_path}",
            "RESTIC_PASSWORD_FILE": str(restic_password_file),
        }
        repository_probe = subprocess.run(
            ["restic", "snapshots"],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if repository_probe.returncode != 0:
            _run_restic(["restic", "init"], environment)
        backup_command = ["restic", "backup", str(staging_directory), "--json"]
        for tag in tags:
            backup_command.extend(("--tag", tag))
        backup_result = _run_restic(backup_command, environment, capture_output=True)
        _run_restic(["restic", "check"], environment)
        if retain:
            _run_restic(
                [
                    "restic",
                    "forget",
                    "--keep-daily",
                    "14",
                    "--keep-weekly",
                    "8",
                    "--keep-monthly",
                    "12",
                    "--prune",
                ],
                environment,
            )
        return _snapshot_id(backup_result.stdout)
    finally:
        config_path.unlink(missing_ok=True)


def request_backup_access(internal_api_url: str, internal_token: str) -> dict[str, Any]:
    response = httpx.post(
        f"{internal_api_url.rstrip('/')}/api/internal/backup-access",
        headers={"Authorization": f"Bearer {internal_token}"},
        timeout=30.0,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DriveUploadError("The dojo API did not provide backup access.") from exc
    payload = cast(dict[str, Any], response.json())
    if not all(
        isinstance(payload.get(field), str) and payload[field]
        for field in ("access_token", "folder_id")
    ):
        raise DriveUploadError("The dojo API returned incomplete backup access.")
    if not isinstance(payload.get("expires_in"), int):
        raise DriveUploadError("The dojo API returned an invalid backup token lifetime.")
    return payload


def _write_rclone_config(access_token: str, folder_id: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w", prefix="dojo-rclone-", suffix=".conf", delete=False
    )
    path = Path(handle.name)
    try:
        os.chmod(path, 0o600)
        token = json.dumps(
            {
                "access_token": access_token,
                "token_type": "Bearer",
            }
        )
        handle.write(
            "[gdrive]\n"
            "type = drive\n"
            "scope = drive.file\n"
            f"root_folder_id = {folder_id}\n"
            f"token = {token}\n"
        )
        handle.close()
    except Exception:
        handle.close()
        path.unlink(missing_ok=True)
        raise
    return path


def _run_restic(
    command: list[str], environment: dict[str, str], *, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DriveUploadError(f"Restic command failed: {command[1]}") from exc
    if not capture_output:
        result.stdout = ""
    return result


def _snapshot_id(output: str) -> str:
    for line in reversed(output.splitlines()):
        try:
            payload = cast(dict[str, Any], json.loads(line))
        except json.JSONDecodeError:
            continue
        if payload.get("message_type") == "summary" and isinstance(payload.get("snapshot_id"), str):
            return cast(str, payload["snapshot_id"])
    raise DriveUploadError("Restic did not return a snapshot ID.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload a prepared dojo backup to Google Drive")
    parser.add_argument("--staging-directory", required=True, type=Path)
    parser.add_argument("--internal-api-url", required=True)
    parser.add_argument("--internal-token-file", required=True, type=Path)
    parser.add_argument("--restic-password-file", required=True, type=Path)
    parser.add_argument("--repository-path", required=True)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--retain", action="store_true")
    args = parser.parse_args()
    snapshot_id = upload_backup(
        args.staging_directory,
        internal_api_url=args.internal_api_url,
        internal_token=args.internal_token_file.read_text(encoding="utf-8").strip(),
        restic_password_file=args.restic_password_file,
        repository_path=args.repository_path,
        tags=tuple(args.tag),
        retain=args.retain,
    )
    print(snapshot_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
