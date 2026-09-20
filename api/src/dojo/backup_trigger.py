from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from urllib.parse import quote

import httpx


class BackupTriggerError(RuntimeError):
    """Raised when the Kubernetes backup Job cannot be queued."""


def request_backup_trigger(*, url: str, token_file: Path, run_id: str) -> str:
    try:
        token = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise BackupTriggerError("Manual backup retry is not available.") from exc
    if not token:
        raise BackupTriggerError("Manual backup retry is not available.")
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"run_id": run_id},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise BackupTriggerError("Manual backup retry could not be queued.") from exc
    if not isinstance(payload, dict):
        raise BackupTriggerError("The backup trigger returned an invalid response.")
    name = payload.get("job_name")
    if not isinstance(name, str) or not name:
        raise BackupTriggerError("The backup trigger returned an invalid Job.")
    return name


def trigger_backup(
    *,
    api_url: str,
    namespace: str,
    cronjob_name: str,
    token_file: Path,
    ca_file: Path,
    run_id: str,
) -> str:
    try:
        token = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise BackupTriggerError("Manual backup retry is not available.") from exc
    if not token:
        raise BackupTriggerError("Manual backup retry is not available.")

    verify: str | bool = str(ca_file) if ca_file.is_file() else True
    headers = {"Authorization": f"Bearer {token}"}
    base_url = api_url.rstrip("/")
    jobs_url = f"{base_url}/apis/batch/v1/namespaces/{quote(namespace, safe='')}/jobs"
    try:
        active_jobs_response = httpx.get(
            jobs_url,
            params={"labelSelector": f"dojo.backup/trigger=manual,dojo.backup/run-id={run_id}"},
            headers=headers,
            verify=verify,
            timeout=10,
        )
        active_jobs_response.raise_for_status()
        active_jobs = cast(dict[str, Any], active_jobs_response.json()).get("items", [])
    except (httpx.HTTPError, ValueError) as exc:
        raise BackupTriggerError("Manual backup retry is not available.") from exc
    if not isinstance(active_jobs, list):
        raise BackupTriggerError("The Kubernetes API returned an invalid backup Job list.")
    for active_job in active_jobs:
        if not isinstance(active_job, dict):
            continue
        status = active_job.get("status")
        metadata = active_job.get("metadata")
        name = metadata.get("name") if isinstance(metadata, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        if not isinstance(labels, dict) or labels.get("dojo.backup/run-id") != run_id:
            continue
        conditions = status.get("conditions", []) if isinstance(status, dict) else []
        terminal = isinstance(conditions, list) and any(
            isinstance(condition, dict)
            and condition.get("status") == "True"
            and condition.get("type") in {"Complete", "Failed"}
            for condition in conditions
        )
        if not terminal and isinstance(name, str):
            return name

    resource_url = (
        f"{base_url}/apis/batch/v1/namespaces/{quote(namespace, safe='')}/cronjobs/"
        f"{quote(cronjob_name, safe='')}"
    )
    try:
        cronjob_response = httpx.get(resource_url, headers=headers, verify=verify, timeout=10)
        cronjob_response.raise_for_status()
        cronjob = cast(dict[str, Any], cronjob_response.json())
    except (httpx.HTTPError, ValueError) as exc:
        raise BackupTriggerError("Manual backup retry is not available.") from exc

    cronjob_spec = cronjob.get("spec")
    job_template = cronjob_spec.get("jobTemplate") if isinstance(cronjob_spec, dict) else None
    template_spec = job_template.get("spec") if isinstance(job_template, dict) else None
    if not isinstance(template_spec, dict):
        raise BackupTriggerError("The deployed backup schedule is invalid.")

    job_spec = deepcopy(template_spec)
    job_spec["ttlSecondsAfterFinished"] = 86400
    pod_template = job_spec.get("template")
    pod_spec = pod_template.get("spec") if isinstance(pod_template, dict) else None
    containers = pod_spec.get("containers") if isinstance(pod_spec, dict) else None
    if not isinstance(containers, list) or not containers or not isinstance(containers[0], dict):
        raise BackupTriggerError("The deployed backup schedule is invalid.")
    env = containers[0].setdefault("env", [])
    if not isinstance(env, list):
        raise BackupTriggerError("The deployed backup schedule is invalid.")
    env.append({"name": "DOJO_BACKUP_TRIGGER_KIND", "value": "MANUAL"})
    env.append({"name": "DOJO_BACKUP_RUN_ID", "value": run_id})
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": f"{cronjob_name}-manual-{run_id}",
            "labels": {
                "dojo.backup/trigger": "manual",
                "dojo.backup/run-id": run_id,
            },
        },
        "spec": job_spec,
    }
    try:
        job_response = httpx.post(
            jobs_url,
            headers=headers,
            json=job,
            verify=verify,
            timeout=10,
        )
        job_response.raise_for_status()
        created_job = cast(dict[str, Any], job_response.json())
    except (httpx.HTTPError, ValueError) as exc:
        raise BackupTriggerError("Manual backup retry could not be queued.") from exc

    metadata = created_job.get("metadata")
    name = metadata.get("name") if isinstance(metadata, dict) else None
    if not isinstance(name, str) or not name:
        raise BackupTriggerError("The Kubernetes API returned an invalid backup Job.")
    return name
