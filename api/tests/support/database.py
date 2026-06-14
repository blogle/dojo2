from __future__ import annotations

from pathlib import Path

from dojo.migrations import provision_database
from dojo.service import DojoService


def provisioned_database_path(base_dir: Path, name: str = "dojo-test.duckdb") -> Path:
    duckdb_path = base_dir / name
    provision_database(str(duckdb_path))
    return duckdb_path


def build_service(base_dir: Path, clock: object, *, name: str = "dojo-test.duckdb") -> DojoService:
    duckdb_path = provisioned_database_path(base_dir, name=name)
    return DojoService(str(duckdb_path), clock=clock)
