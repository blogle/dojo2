import sys
from pathlib import Path

import httpx

from dojo import backup_status


def test_status_reporter_accepts_skipped_locked(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_post(url: str, *, headers: dict[str, str], json: dict[str, object], timeout: int):
        captured.update(url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(backup_status.httpx, "post", fake_post)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dojo-backup-status",
            "--url",
            "http://dojo/api/internal/backup-runs",
            "--token-file",
            str(token_file),
            "--run-id",
            "00000000-0000-4000-8000-000000000001",
            "--trigger-kind",
            "SCHEDULED",
            "--status",
            "SKIPPED",
            "--phase",
            "LOCKED",
            "--error-message",
            "MANUAL:run-2 owns the backup lock",
        ],
    )
    assert backup_status.main() == 0
    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["status"] == "SKIPPED"
    assert payload["phase"] == "LOCKED"
