from __future__ import annotations

import builtins
import io
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from dojo.backup_lock import (
    LEASE_DURATION_SECONDS,
    LEASE_RENEW_INTERVAL_SECONDS,
    KubernetesLease,
    holder_identity,
    lease_is_expired,
)
from dojo.clock import FrozenClock

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class FakeKubernetesLease(KubernetesLease):
    def __init__(self, responses: list[tuple[int, dict[str, Any]]]) -> None:
        super().__init__("default", FrozenClock(NOW))
        self.responses = responses
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any]]:
        self.calls.append((method, path, body))
        return self.responses.pop(0)


def lease(
    holder: str,
    *,
    version: str = "1",
    renewed_at: datetime = NOW,
    acquired_at: datetime = NOW - timedelta(minutes=1),
) -> dict[str, Any]:
    return {
        "apiVersion": "coordination.k8s.io/v1",
        "kind": "Lease",
        "metadata": {"name": "dojo-backup-global", "resourceVersion": version},
        "spec": {
            "holderIdentity": holder,
            "leaseDurationSeconds": LEASE_DURATION_SECONDS,
            "acquireTime": acquired_at.isoformat().replace("+00:00", "Z"),
            "renewTime": renewed_at.isoformat().replace("+00:00", "Z"),
            "leaseTransitions": 2,
        },
    }


def test_holder_identity_includes_trigger_run_and_orchestration_identity() -> None:
    assert holder_identity("manual", "run-123", "dojo-backup-1", "pod-abc") == (
        "MANUAL:run-123:job=dojo-backup-1:pod=pod-abc"
    )


def test_lease_expiry_boundary_is_deterministic() -> None:
    current = lease("MANUAL:run-1", renewed_at=NOW)
    assert not lease_is_expired(current, NOW + timedelta(seconds=LEASE_DURATION_SECONDS - 1))
    assert lease_is_expired(current, NOW + timedelta(seconds=LEASE_DURATION_SECONDS))
    assert LEASE_RENEW_INTERVAL_SECONDS < LEASE_DURATION_SECONDS


@pytest.mark.parametrize(
    ("candidate", "owner"),
    [("SCHEDULED:run-s", "MANUAL:run-m"), ("MANUAL:run-m", "SCHEDULED:run-s")],
)
def test_valid_foreign_holder_refuses_acquisition(candidate: str, owner: str) -> None:
    lock = FakeKubernetesLease([(200, lease(owner, renewed_at=NOW - timedelta(seconds=10)))])

    decision = lock.acquire_or_renew(candidate, NOW)

    assert not decision.acquired
    assert decision.holder == owner
    assert [call[0] for call in lock.calls] == ["GET"]


def test_stale_lease_takeover_put_uses_observed_resource_version() -> None:
    expired = lease("MANUAL:abandoned", version="rv-stale", renewed_at=NOW - timedelta(seconds=301))
    lock = FakeKubernetesLease([(200, expired), (200, lease("SCHEDULED:new", version="rv-2"))])

    decision = lock.acquire_or_renew("SCHEDULED:new", NOW)

    assert decision.acquired
    put = lock.calls[1]
    assert put[0] == "PUT"
    assert put[2] is not None
    assert put[2]["metadata"]["resourceVersion"] == "rv-stale"


def test_stale_takeover_conflict_rereads_renewed_foreign_holder() -> None:
    expired = lease("MANUAL:owner", version="rv-stale", renewed_at=NOW - timedelta(seconds=301))
    renewed = lease("MANUAL:owner", version="rv-renewed", renewed_at=NOW)
    lock = FakeKubernetesLease([(200, expired), (409, {}), (200, renewed)])

    decision = lock.acquire_or_renew("SCHEDULED:new", NOW)

    assert not decision.acquired
    assert decision.holder == "MANUAL:owner"
    assert [call[0] for call in lock.calls] == ["GET", "PUT", "GET"]


def test_same_holder_renews_and_preserves_acquire_time() -> None:
    current = lease("MANUAL:run-1", version="rv-1")
    lock = FakeKubernetesLease([(200, current), (200, lease("MANUAL:run-1", version="rv-2"))])

    decision = lock.acquire_or_renew("MANUAL:run-1", NOW)

    assert decision.acquired
    body = lock.calls[1][2]
    assert body is not None
    assert body["spec"]["acquireTime"] == current["spec"]["acquireTime"]
    assert body["spec"]["renewTime"] == "2026-01-01T00:00:00Z"
    assert body["metadata"]["resourceVersion"] == "rv-1"


def test_release_does_not_clear_a_new_owners_lease() -> None:
    lock = FakeKubernetesLease([(200, lease("SCHEDULED:new-owner", version="rv-new"))])

    lock.release("MANUAL:old-owner", NOW)

    assert [call[0] for call in lock.calls] == ["GET"]


def test_request_uses_service_account_ca_for_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    lock = KubernetesLease("default", FrozenClock(NOW))
    lock.base_url = "https://kubernetes.default.svc"
    lock.token_path = "/serviceaccount/token"
    observed: dict[str, Any] = {}
    fake_context = object()

    class Response(io.BytesIO):
        status = 200

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            self.close()

    monkeypatch.setattr(builtins, "open", lambda *_args, **_kwargs: io.StringIO("worker-token"))

    def create_context(*, cafile: str) -> object:
        observed["cafile"] = cafile
        return fake_context

    def fake_urlopen(request: Any, *, timeout: int, context: object) -> Response:
        observed.update(request=request, timeout=timeout, context=context)
        return Response(json.dumps({"ok": True}).encode())

    monkeypatch.setattr("dojo.backup_lock.ssl.create_default_context", create_context)
    monkeypatch.setattr("dojo.backup_lock.urlopen", fake_urlopen)

    status, body = lock._request("GET", "/leases/dojo-backup-global")

    assert status == 200
    assert body == {"ok": True}
    assert observed["cafile"] == "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    assert observed["context"] is fake_context
    assert observed["request"].get_header("Authorization") == "Bearer worker-token"
