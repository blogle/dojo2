from __future__ import annotations

from pathlib import Path

import pytest

from dojo.backup import prepare_backup, restore_backup, verify_backup
from dojo.migrations import provision_database


def test_prepare_verify_and_restore_backup(tmp_path: Path) -> None:
    source = tmp_path / "source.duckdb"
    prepared = tmp_path / "prepared" / "dojo.duckdb"
    restored = tmp_path / "restored" / "dojo.duckdb"
    provision_database(str(source))

    manifest = prepare_backup(
        source,
        prepared,
        image_digest="sha256:test",
        source_snapshot="snapshot-test",
    )

    metadata = verify_backup(prepared, manifest)
    assert metadata["image_digest"] == "sha256:test"
    assert metadata["source_snapshot"] == "snapshot-test"
    restore_backup(prepared, manifest, restored)
    assert restored.is_file()


def test_verify_rejects_tampered_database(tmp_path: Path) -> None:
    source = tmp_path / "source.duckdb"
    prepared = tmp_path / "prepared.duckdb"
    provision_database(str(source))
    manifest = prepare_backup(
        source,
        prepared,
        image_digest="sha256:test",
        source_snapshot="snapshot-test",
    )
    prepared.write_bytes(prepared.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="size"):
        verify_backup(prepared, manifest)


def test_restore_refuses_existing_target(tmp_path: Path) -> None:
    source = tmp_path / "source.duckdb"
    prepared = tmp_path / "prepared.duckdb"
    target = tmp_path / "target.duckdb"
    provision_database(str(source))
    manifest = prepare_backup(
        source,
        prepared,
        image_digest="sha256:test",
        source_snapshot="snapshot-test",
    )
    target.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="must not already exist"):
        restore_backup(prepared, manifest, target)
    assert target.read_text(encoding="utf-8") == "keep"
