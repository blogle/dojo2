from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops/k8s/snapshot-backup.sh"
BUILD_SHA = "a" * 40


def render_job(*, build_sha: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DOJO_BUILD_SHA": build_sha,
            "DOJO_BACKUP_JOB_NAME": "dojo-backup-test",
            "DOJO_BACKUP_RUN_ID": "00000000-0000-4000-8000-000000000001",
            "DOJO_BACKUP_SNAPSHOT": "dojo-data-test",
            "DOJO_BACKUP_CLONE": "dojo-backup-test",
        }
    )
    return subprocess.run(
        ["bash", str(SCRIPT), "--render-job"],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def test_rendered_backup_job_uses_its_build_sha() -> None:
    result = render_job(build_sha=BUILD_SHA)

    assert result.returncode == 0, result.stderr
    assert f"image: ghcr.io/blogle/dojo2:git-{BUILD_SHA}" in result.stdout
    assert "imagePullPolicy: Always" in result.stdout


def test_missing_build_sha_fails_before_kubernetes_calls(tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("status-token", encoding="utf-8")
    status_log = tmp_path / "status.log"
    kubectl_marker = tmp_path / "kubectl-called"
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    status_command = command_dir / "status"
    status_command.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$STATUS_LOG"\n',
        encoding="utf-8",
    )
    status_command.chmod(0o755)
    kubectl_command = command_dir / "kubectl"
    kubectl_command.write_text(
        f"#!/usr/bin/env bash\ntouch {kubectl_marker}\nexit 99\n",
        encoding="utf-8",
    )
    kubectl_command.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{command_dir}:{environment['PATH']}",
            "DOJO_BACKUP_RUN_ID": "00000000-0000-4000-8000-000000000002",
            "DOJO_BACKUP_STATUS_TOKEN_FILE": str(token_file),
            "DOJO_BACKUP_STATUS_COMMAND": str(status_command),
            "STATUS_LOG": str(status_log),
        }
    )
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert result.returncode != 0
    assert "DOJO_BUILD_SHA must be the full 40-character lowercase Git SHA" in result.stderr
    status_report = status_log.read_text(encoding="utf-8")
    assert "--status RUNNING" in status_report
    assert "--phase STARTING" in status_report
    assert "--status FAILED" in status_report
    assert "DOJO_BUILD_SHA must be the full 40-character lowercase Git SHA" in status_report
    assert not kubectl_marker.exists()


def test_backup_script_has_no_runtime_image_discovery_path() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "get deployment dojo" not in source
    assert "containerStatuses" not in source
    assert "imageID" not in source
