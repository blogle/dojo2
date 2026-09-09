from __future__ import annotations

import argparse
from pathlib import Path

import httpx


def report_backup_status(
    *,
    url: str,
    token_file: Path,
    run_id: str,
    trigger_kind: str,
    status: str,
    phase: str,
    source_snapshot: str | None = None,
    image_digest: str | None = None,
    restic_snapshot_id: str | None = None,
    database_sha256: str | None = None,
    database_size_bytes: int | None = None,
    error_message: str | None = None,
) -> None:
    token = token_file.read_text(encoding="utf-8").strip()
    response = httpx.post(
        f"{url.rstrip('/')}/{run_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "trigger_kind": trigger_kind,
            "status": status,
            "phase": phase,
            "source_snapshot": source_snapshot,
            "image_digest": image_digest,
            "restic_snapshot_id": restic_snapshot_id,
            "database_sha256": database_sha256,
            "database_size_bytes": database_size_bytes,
            "error_message": error_message,
        },
        timeout=10,
    )
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Report a dojo backup run")
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trigger-kind", choices=["SCHEDULED", "MANUAL"], required=True)
    parser.add_argument("--status", choices=["RUNNING", "SUCCEEDED", "FAILED"], required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--source-snapshot")
    parser.add_argument("--image-digest")
    parser.add_argument("--restic-snapshot-id")
    parser.add_argument("--database-sha256")
    parser.add_argument("--database-size-bytes", type=int)
    parser.add_argument("--error-message")
    args = parser.parse_args()
    report_backup_status(
        url=args.url,
        token_file=args.token_file,
        run_id=args.run_id,
        trigger_kind=args.trigger_kind,
        status=args.status,
        phase=args.phase,
        source_snapshot=args.source_snapshot,
        image_digest=args.image_digest,
        restic_snapshot_id=args.restic_snapshot_id,
        database_sha256=args.database_sha256,
        database_size_bytes=args.database_size_bytes,
        error_message=args.error_message,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
