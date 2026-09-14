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


def restore_backup_snapshot(
    snapshot_id: str,
    target_directory: Path,
    *,
    internal_api_url: str,
    internal_token: str,
    restic_password_file: Path,
    repository_path: str,
) -> None:
    access = request_backup_access(internal_api_url, internal_token)
    config_path = _write_rclone_config(access["access_token"], access["folder_id"])
    try:
        environment = os.environ | {
            "RCLONE_CONFIG": str(config_path),
            "RESTIC_REPOSITORY": f"rclone:gdrive:{repository_path}",
            "RESTIC_PASSWORD_FILE": str(restic_password_file),
        }
        target_directory.mkdir(parents=True, exist_ok=False)
        _run_restic(
            ["restic", "restore", snapshot_id, "--target", str(target_directory)],
            environment,
        )
    finally:
        config_path.unlink(missing_ok=True)


def purge_repository(
    repository_path: str,
    *,
    internal_api_url: str,
    internal_token: str,
) -> None:
    if repository_path == "dojo/restic" or not repository_path.startswith("dojo-rehearsals/"):
        raise DriveUploadError("Only a rehearsal repository may be removed.")
    access = request_backup_access(internal_api_url, internal_token)
    config_path = _write_rclone_config(access["access_token"], access["folder_id"])
    try:
        environment = os.environ | {"RCLONE_CONFIG": str(config_path)}
        try:
            subprocess.run(
                ["rclone", "purge", f"gdrive:{repository_path}"],
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise DriveUploadError("Rehearsal repository cleanup failed.") from exc
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
    parser = argparse.ArgumentParser(description="Upload prepared dojo backup data to Google Drive")
    subparsers = parser.add_subparsers(dest="command", required=True)
    upload = subparsers.add_parser("upload")
    upload.add_argument("--staging-directory", required=True, type=Path)
    upload.add_argument("--internal-api-url", required=True)
    upload.add_argument("--internal-token-file", required=True, type=Path)
    upload.add_argument("--restic-password-file", required=True, type=Path)
    upload.add_argument("--repository-path", required=True)
    upload.add_argument("--tag", action="append", default=[])
    upload.add_argument("--retain", action="store_true")
    restore = subparsers.add_parser("restore")
    restore.add_argument("--snapshot-id", required=True)
    restore.add_argument("--target-directory", required=True, type=Path)
    restore.add_argument("--internal-api-url", required=True)
    restore.add_argument("--internal-token-file", required=True, type=Path)
    restore.add_argument("--restic-password-file", required=True, type=Path)
    restore.add_argument("--repository-path", required=True)
    purge = subparsers.add_parser("purge")
    purge.add_argument("--internal-api-url", required=True)
    purge.add_argument("--internal-token-file", required=True, type=Path)
    purge.add_argument("--repository-path", required=True)
    args = parser.parse_args()
    internal_token = args.internal_token_file.read_text(encoding="utf-8").strip()
    if args.command == "upload":
        snapshot_id = upload_backup(
            args.staging_directory,
            internal_api_url=args.internal_api_url,
            internal_token=internal_token,
            restic_password_file=args.restic_password_file,
            repository_path=args.repository_path,
            tags=tuple(args.tag),
            retain=args.retain,
        )
        print(snapshot_id)
    elif args.command == "restore":
        restore_backup_snapshot(
            args.snapshot_id,
            args.target_directory,
            internal_api_url=args.internal_api_url,
            internal_token=internal_token,
            restic_password_file=args.restic_password_file,
            repository_path=args.repository_path,
        )
    else:
        purge_repository(
            args.repository_path,
            internal_api_url=args.internal_api_url,
            internal_token=internal_token,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
