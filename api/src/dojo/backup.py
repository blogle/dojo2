from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, cast

import duckdb

from dojo.clock import SystemClock
from dojo.sql import load_sql


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_path(database_path: Path) -> Path:
    return database_path.with_name(f"{database_path.name}.manifest.json")


def _required_scalar(connection: duckdb.DuckDBPyConnection, sql_name: str) -> Any:
    row = connection.execute(load_sql(sql_name)).fetchone()
    if row is None:
        raise ValueError(f"Backup verification query returned no row: {sql_name}")
    return row[0]


def prepare_backup(
    source: Path,
    destination: Path,
    *,
    image_digest: str,
    source_snapshot: str,
) -> Path:
    if not source.is_file():
        raise ValueError(f"Backup source does not exist: {source}")
    if destination.exists() or _manifest_path(destination).exists():
        raise ValueError("Backup destination must not already exist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    source_wal = source.with_name(f"{source.name}.wal")
    destination_wal = destination.with_name(f"{destination.name}.wal")
    if source_wal.exists():
        shutil.copy2(source_wal, destination_wal)

    connection = duckdb.connect(str(destination))
    try:
        connection.execute(load_sql("control/checkpoint"))
        object_count = int(_required_scalar(connection, "queries/backup_schema_summary"))
        duckdb_version = str(_required_scalar(connection, "queries/duckdb_version"))
    finally:
        connection.close()

    manifest: dict[str, Any] = {
        "format_version": 1,
        "created_at": SystemClock().now().isoformat(),
        "database_file": destination.name,
        "database_size": destination.stat().st_size,
        "database_sha256": _sha256(destination),
        "duckdb_version": duckdb_version,
        "schema_object_count": object_count,
        "image_digest": image_digest,
        "source_snapshot": source_snapshot,
    }
    manifest_path = _manifest_path(destination)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path


def verify_backup(database_path: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported backup manifest format")
    if manifest.get("database_file") != database_path.name:
        raise ValueError("Backup manifest names a different database file")
    if manifest.get("database_size") != database_path.stat().st_size:
        raise ValueError("Backup database size does not match manifest")
    if manifest.get("database_sha256") != _sha256(database_path):
        raise ValueError("Backup database hash does not match manifest")

    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        object_count = int(_required_scalar(connection, "queries/backup_schema_summary"))
    finally:
        connection.close()
    if manifest.get("schema_object_count") != object_count:
        raise ValueError("Backup schema summary does not match manifest")
    return manifest


def restore_backup(database_path: Path, manifest_path: Path, target: Path) -> None:
    verify_backup(database_path, manifest_path)
    if target.exists():
        raise ValueError("Restore target must not already exist")
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_name(f".{target.name}.staged")
    if staged.exists():
        staged.unlink()
    shutil.copy2(database_path, staged)
    os.replace(staged, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and verify recoverable dojo backups")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("destination", type=Path)
    prepare.add_argument("--image-digest", required=True)
    prepare.add_argument("--source-snapshot", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("database", type=Path)
    verify.add_argument("manifest", type=Path)
    restore = subparsers.add_parser("restore")
    restore.add_argument("database", type=Path)
    restore.add_argument("manifest", type=Path)
    restore.add_argument("target", type=Path)
    args = parser.parse_args()

    if args.command == "prepare":
        manifest = prepare_backup(
            args.source,
            args.destination,
            image_digest=args.image_digest,
            source_snapshot=args.source_snapshot,
        )
        print(manifest)
    elif args.command == "verify":
        verify_backup(args.database, args.manifest)
        print("backup verified")
    else:
        restore_backup(args.database, args.manifest, args.target)
        print(args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
