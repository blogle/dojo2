from datetime import UTC, datetime, timedelta

from dojo.backup_lock import (
    LEASE_DURATION_SECONDS,
    holder_identity,
    lease_is_expired,
)


def test_holder_identity_includes_trigger_run_and_orchestration_identity() -> None:
    assert holder_identity("manual", "run-123", "dojo-backup-1", "pod-abc") == (
        "MANUAL:run-123:job=dojo-backup-1:pod=pod-abc"
    )


def test_lease_expiry_boundary_is_deterministic() -> None:
    renewed_at = datetime(2026, 1, 1, tzinfo=UTC)
    lease = {
        "spec": {
            "renewTime": renewed_at.isoformat().replace("+00:00", "Z"),
            "leaseDurationSeconds": LEASE_DURATION_SECONDS,
        }
    }
    assert not lease_is_expired(lease, renewed_at + timedelta(seconds=LEASE_DURATION_SECONDS - 1))
    assert lease_is_expired(lease, renewed_at + timedelta(seconds=LEASE_DURATION_SECONDS))
