from __future__ import annotations

from pathlib import Path

import dojo.backup_trigger as backup_trigger


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_trigger_backup_clones_cronjob_template(monkeypatch, tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("service-token", encoding="utf-8")
    requests: list[dict[str, object]] = []

    def get(url, **kwargs):
        requests.append({"method": "GET", "url": url, **kwargs})
        if url.endswith("/jobs"):
            return FakeResponse({"items": []})
        return FakeResponse(
            {
                "spec": {
                    "jobTemplate": {
                        "spec": {
                            "backoffLimit": 0,
                            "template": {
                                "spec": {
                                    "restartPolicy": "Never",
                                    "containers": [{"name": "orchestrator", "env": []}],
                                }
                            },
                        }
                    }
                }
            }
        )

    def post(url, **kwargs):
        requests.append({"method": "POST", "url": url, **kwargs})
        return FakeResponse({"metadata": {"name": "dojo-backup-manual-abc"}})

    monkeypatch.setattr(backup_trigger.httpx, "get", get)
    monkeypatch.setattr(backup_trigger.httpx, "post", post)

    name = backup_trigger.trigger_backup(
        api_url="https://kubernetes.default.svc/",
        namespace="dojo-staging",
        cronjob_name="dojo-backup",
        token_file=token_file,
        ca_file=tmp_path / "missing-ca.crt",
    )

    assert name == "dojo-backup-manual-abc"
    assert requests[1]["url"] == (
        "https://kubernetes.default.svc/apis/batch/v1/namespaces/dojo-staging/cronjobs/dojo-backup"
    )
    job = requests[2]["json"]
    assert isinstance(job, dict)
    assert job["metadata"] == {
        "generateName": "dojo-backup-manual-",
        "labels": {"dojo.backup/trigger": "manual"},
    }
    assert job["spec"]["ttlSecondsAfterFinished"] == 86400
    assert job["spec"]["template"]["spec"]["containers"][0]["env"] == [
        {"name": "DOJO_BACKUP_TRIGGER_KIND", "value": "MANUAL"}
    ]
    assert requests[0]["headers"] == {"Authorization": "Bearer service-token"}
