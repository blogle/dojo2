"""Kubernetes Lease coordination for the shared backup worker."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

LEASE_NAME = "dojo-backup-global"
LEASE_DURATION_SECONDS = 300
LEASE_RENEW_INTERVAL_SECONDS = 30
API_PATH = "/apis/coordination.k8s.io/v1/namespaces/{namespace}/leases"


@dataclass(frozen=True)
class LeaseDecision:
    acquired: bool
    holder: str
    expires_at: datetime | None


def holder_identity(trigger_kind: str, run_id: str, job: str, pod: str) -> str:
    return f"{trigger_kind.upper()}:{run_id}:job={job or 'unknown'}:pod={pod or 'unknown'}"


def lease_is_expired(lease: dict[str, Any], now: datetime) -> bool:
    spec = lease.get("spec", {})
    renewed = spec.get("renewTime") or spec.get("acquireTime")
    duration = int(spec.get("leaseDurationSeconds", LEASE_DURATION_SECONDS))
    if not renewed:
        return True
    renewed_at = datetime.fromisoformat(renewed.replace("Z", "+00:00"))
    return now >= renewed_at + timedelta(seconds=duration)


def lease_expiry(lease: dict[str, Any]) -> datetime | None:
    spec = lease.get("spec", {})
    renewed = spec.get("renewTime") or spec.get("acquireTime")
    if not renewed:
        return None
    return datetime.fromisoformat(renewed.replace("Z", "+00:00")) + timedelta(
        seconds=int(spec.get("leaseDurationSeconds", LEASE_DURATION_SECONDS))
    )


class KubernetesLease:
    def __init__(self, namespace: str) -> None:
        self.namespace = namespace
        self.base_url = os.environ.get("KUBERNETES_SERVICE_HOST", "")
        port = os.environ.get("KUBERNETES_SERVICE_PORT_HTTPS", "443")
        self.base_url = f"https://{self.base_url}:{port}"
        self.token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any]]:
        with open(self.token_path, encoding="utf-8") as token_file:
            token = token_file.read().strip()
        data = json.dumps(body).encode() if body is not None else None
        request = Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            response_body = json.loads(error.read() or b"{}")
            return error.code, response_body

    @property
    def collection(self) -> str:
        return API_PATH.format(namespace=self.namespace)

    def acquire_or_renew(self, holder: str, now: datetime | None = None) -> LeaseDecision:
        now = now or datetime.now(UTC)
        timestamp = now.isoformat(timespec="seconds").replace("+00:00", "Z")
        lease_path = f"{self.collection}/{LEASE_NAME}"
        for _ in range(5):
            status, lease = self._request("GET", lease_path)
            if status == 404:
                body = self._body(holder, timestamp)
                status, created = self._request("POST", self.collection, body)
                if status == 201:
                    return LeaseDecision(
                        acquired=True, holder=holder, expires_at=lease_expiry(created)
                    )
                if status == 409:
                    continue
                raise RuntimeError(f"Could not create backup Lease: {created}")
            if status != 200:
                raise RuntimeError(f"Could not read backup Lease: {lease}")
            current_holder = lease.get("spec", {}).get("holderIdentity", "")
            if current_holder != holder and not lease_is_expired(lease, now):
                return LeaseDecision(
                    acquired=False,
                    holder=current_holder,
                    expires_at=lease_expiry(lease),
                )
            body = self._body(holder, timestamp, lease)
            status, updated = self._request("PUT", lease_path, body)
            if status == 200:
                return LeaseDecision(acquired=True, holder=holder, expires_at=lease_expiry(updated))
            if status != 409:
                raise RuntimeError(f"Could not update backup Lease: {updated}")
        raise RuntimeError("Backup Lease changed repeatedly during acquisition; retry this backup.")

    def release(self, holder: str) -> None:
        path = f"{self.collection}/{LEASE_NAME}"
        for _ in range(5):
            status, lease = self._request("GET", path)
            if status == 404:
                return
            if status != 200:
                raise RuntimeError(f"Could not read backup Lease for release: {lease}")
            if lease.get("spec", {}).get("holderIdentity") != holder:
                return
            spec = lease.get("spec", {})
            spec.update(
                {
                    "holderIdentity": "",
                    "renewTime": datetime.now(UTC)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z"),
                }
            )
            status, response = self._request("PUT", path, lease)
            if status == 200:
                return
            if status != 409:
                raise RuntimeError(f"Could not release backup Lease: {response}")
        raise RuntimeError("Backup Lease changed repeatedly during release.")

    @staticmethod
    def _body(holder: str, timestamp: str, current: dict[str, Any] | None = None) -> dict[str, Any]:
        metadata = {"name": LEASE_NAME}
        spec: dict[str, Any] = {
            "holderIdentity": holder,
            "leaseDurationSeconds": LEASE_DURATION_SECONDS,
            "acquireTime": timestamp,
            "renewTime": timestamp,
            "leaseTransitions": 0,
        }
        if current:
            metadata["resourceVersion"] = current.get("metadata", {}).get("resourceVersion")
            old_spec = current.get("spec", {})
            spec["acquireTime"] = old_spec.get("acquireTime", timestamp)
            spec["leaseTransitions"] = int(old_spec.get("leaseTransitions", 0)) + int(
                old_spec.get("holderIdentity", "") != holder
            )
        return {
            "apiVersion": "coordination.k8s.io/v1",
            "kind": "Lease",
            "metadata": metadata,
            "spec": spec,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("acquire", "renew", "release"))
    parser.add_argument("--holder", required=True)
    parser.add_argument("--namespace", default=os.environ.get("DOJO_NAMESPACE", "default"))
    args = parser.parse_args()
    lease = KubernetesLease(args.namespace)
    if args.action == "release":
        lease.release(args.holder)
        return
    decision = lease.acquire_or_renew(args.holder)
    if not decision.acquired:
        expiry = decision.expires_at.isoformat() if decision.expires_at else "unknown expiry"
        print(f"Backup lock held by {decision.holder} until {expiry}", file=sys.stderr)
        raise SystemExit(3)


if __name__ == "__main__":
    main()
