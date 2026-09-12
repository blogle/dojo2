from __future__ import annotations

import subprocess

import pytest

from dojo.drive_backup import verify_drive_folder


def test_verify_drive_folder_probes_write_access(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []

    def run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(
        "dojo.drive_backup._refresh_access_token",
        lambda *_args, **_kwargs: "fake-access-token",
    )
    verify_drive_folder(
        "folder-id",
        client_id="test-client-id",
        client_secret="test-client-secret",
        refresh_token="test-refresh-token",
    )

    assert [command[1] for command in calls] == ["lsf", "mkdir", "rcat", "delete", "rmdir"]


def test_verify_drive_folder_rejects_failed_probe(monkeypatch, tmp_path) -> None:
    def fail(command, **_kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(
        "dojo.drive_backup._refresh_access_token",
        lambda *_args, **_kwargs: "fake-access-token",
    )
    with pytest.raises(ValueError, match="could not write"):
        verify_drive_folder(
            "folder-id",
            client_id="test-client-id",
            client_secret="test-client-secret",
            refresh_token="test-refresh-token",
        )
