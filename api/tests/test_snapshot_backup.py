from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops/k8s/snapshot-backup.sh"
RBAC = REPO_ROOT / "deploy/k8s/base/backup-rbac.yaml"
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
            "DOJO_BACKUP_LOCK_HOLDER": "MANUAL:run-test:job=dojo-backup-test:pod=pod-test",
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
    assert "serviceAccountName: dojo-backup" in result.stdout
    assert "child_lock_holder='MANUAL:run-test:job=dojo-backup-test:pod=pod-test'" in result.stdout
    assert '"$child_lock_command" renew --holder "$child_lock_holder" --namespace' in result.stdout
    assert 'kill -TERM "$child_pid"' in result.stdout


def test_rendered_child_lock_guard_terminates_on_renewal_loss(tmp_path: Path) -> None:
    rendered = render_job(build_sha=BUILD_SHA)
    assert rendered.returncode == 0, rendered.stderr
    guard = rendered.stdout.split("          # BEGIN shared backup Lease guard\n", 1)[1].split(
        "          # END shared backup Lease guard\n", 1
    )[0]
    guard_script = textwrap.dedent(guard) + "sleep 0.25\n"
    command = tmp_path / "lock"
    counter = tmp_path / "renew-count"
    command.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$1" == renew ]]; then\n'
        f"  count=0; [[ -f '{counter}' ]] && count=\"$(< '{counter}')\"\n"
        "  count=$((count + 1))\n"
        f"  printf '%s' \"$count\" > '{counter}'\n"
        '  [[ "$count" -eq 1 ]] && exit 0\n'
        "  exit 9\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    command.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "DOJO_BACKUP_LOCK_COMMAND": str(command),
            "DOJO_BACKUP_LOCK_RENEW_INTERVAL_SECONDS": "0.05",
        }
    )

    result = subprocess.run(
        ["bash", "-c", guard_script],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
        timeout=3,
    )

    assert result.returncode != 0
    assert int(counter.read_text(encoding="utf-8")) >= 2


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
    lock_command = command_dir / "lock"
    lock_command.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    lock_command.chmod(0o755)
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
            "DOJO_BACKUP_LOCK_COMMAND": str(lock_command),
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


@pytest.mark.parametrize(
    ("trigger_kind", "holder_kind"),
    [("SCHEDULED", "MANUAL"), ("MANUAL", "SCHEDULED")],
)
def test_lock_contention_skips_without_kubernetes_calls(
    tmp_path: Path, trigger_kind: str, holder_kind: str
) -> None:
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    status_log = tmp_path / "status.log"
    kubectl_marker = tmp_path / "kubectl-called"
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    lock_command = command_dir / "lock"
    lock_command.write_text(
        f'#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$ORDER_LOG"\n'
        f"if [[ \"$1\" == acquire ]]; then printf '%s\\n' '{holder_kind}:run-owner owns lock' >&2; exit 3; fi\n",
        encoding="utf-8",
    )
    lock_command.chmod(0o755)
    status_command = command_dir / "status"
    status_command.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$STATUS_LOG"\n',
        encoding="utf-8",
    )
    status_command.chmod(0o755)
    kubectl_command = command_dir / "kubectl"
    kubectl_command.write_text(
        f"#!/usr/bin/env bash\ntouch '{kubectl_marker}'\nexit 99\n", encoding="utf-8"
    )
    kubectl_command.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{command_dir}:{environment['PATH']}",
            "DOJO_BACKUP_TRIGGER_KIND": trigger_kind,
            "DOJO_BACKUP_RUN_ID": "00000000-0000-4000-8000-000000000035",
            "DOJO_BACKUP_STATUS_TOKEN_FILE": str(token_file),
            "DOJO_BACKUP_STATUS_COMMAND": str(status_command),
            "DOJO_BACKUP_LOCK_COMMAND": str(lock_command),
            "STATUS_LOG": str(status_log),
            "ORDER_LOG": str(tmp_path / "order.log"),
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT)], capture_output=True, text=True, env=environment, check=False
    )

    assert result.returncode == 0, result.stderr
    report = status_log.read_text(encoding="utf-8")
    assert "--status SKIPPED" in report
    assert "--phase LOCKED" in report
    assert f"{holder_kind}:run-owner owns lock" in report
    assert not kubectl_marker.exists()


def test_renewal_loss_cleans_child_job_and_clone_before_releasing_lock(
    tmp_path: Path,
) -> None:
    command_dir = tmp_path / "bin"
    command_dir.mkdir()
    order_log = tmp_path / "order.log"
    status_log = tmp_path / "status.log"
    child_job_created = tmp_path / "child-job-created"
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    lock_command = command_dir / "lock"
    lock_command.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'lock %s\\n' "$1" >> "$ORDER_LOG"
case "$1" in
  acquire) exit 0 ;;
  renew)
    for _ in $(seq 1 500); do
      [[ -f "$CHILD_JOB_CREATED" ]] && break
      sleep 0.01
    done
    [[ -f "$CHILD_JOB_CREATED" ]]
    exit 1
    ;;
  release) exit 0 ;;
esac
""",
        encoding="utf-8",
    )
    lock_command.chmod(0o755)
    status_command = command_dir / "status"
    status_command.write_text(
        '#!/usr/bin/env bash\nprintf \'status %s\\n\' "$*" >> "$ORDER_LOG"\n'
        'printf \'%s\\n\' "$*" >> "$STATUS_LOG"\n',
        encoding="utf-8",
    )
    status_command.chmod(0o755)
    kubectl_command = command_dir / "kubectl"
    kubectl_command.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == *" apply -f -"* ]]; then
  body="$(</dev/stdin)"
  if [[ "$body" == *"kind: Job"* ]]; then
    printf 'kubectl create child-job\\n' >> "$ORDER_LOG"
    touch "$CHILD_JOB_CREATED"
  else
    printf 'kubectl apply resource\\n' >> "$ORDER_LOG"
  fi
elif [[ "$*" == *" get pvc dojo-data "* ]]; then
  printf 'storage-class\\n'
elif [[ "$*" == *" get volumesnapshot "* ]]; then
  printf 'true\\n'
elif [[ "$*" == *" get job "* ]]; then
  sleep 0.2
elif [[ "$*" == *" delete job "* ]]; then
  printf 'kubectl delete job\\n' >> "$ORDER_LOG"
elif [[ "$*" == *" delete pvc "* ]]; then
  printf 'kubectl delete pvc\\n' >> "$ORDER_LOG"
else
  printf 'unexpected kubectl: %s\\n' "$*" >&2
  exit 98
fi
""",
        encoding="utf-8",
    )
    kubectl_command.chmod(0o755)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{command_dir}:{environment['PATH']}",
            "DOJO_BUILD_SHA": BUILD_SHA,
            "DOJO_BACKUP_TRIGGER_KIND": "MANUAL",
            "DOJO_BACKUP_RUN_ID": "00000000-0000-4000-8000-000000000037",
            "DOJO_BACKUP_JOB_NAME": "dojo-backup-manual-test",
            "DOJO_BACKUP_STATUS_TOKEN_FILE": str(token_file),
            "DOJO_BACKUP_STATUS_COMMAND": str(status_command),
            "DOJO_BACKUP_LOCK_COMMAND": str(lock_command),
            "DOJO_BACKUP_LOCK_RENEW_INTERVAL_SECONDS": "0.05",
            "DOJO_VOLUME_SNAPSHOT_CLASS": "snapshot-class",
            "STATUS_LOG": str(status_log),
            "ORDER_LOG": str(order_log),
            "CHILD_JOB_CREATED": str(child_job_created),
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
        timeout=10,
    )

    assert result.returncode != 0
    assert child_job_created.exists()
    events = order_log.read_text(encoding="utf-8").splitlines()
    assert events.index("kubectl delete job") < events.index("kubectl delete pvc")
    assert events.index("kubectl delete pvc") < events.index("lock release")


def test_backup_script_has_no_runtime_image_discovery_path() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "get deployment dojo" not in source
    assert "containerStatuses" not in source
    assert "imageID" not in source


def test_backup_role_keeps_transitional_deployment_read() -> None:
    source = RBAC.read_text(encoding="utf-8")

    assert 'apiGroups: ["apps"]' in source
    assert 'resources: ["deployments"]' in source
    assert 'verbs: ["get"]' in source
