"""Pure SCD algebra model with property-based testing.

This module defines a pure model of SCD operations (Create, Edit, Delete, Restore)
and uses Hypothesis to generate random operation sequences while verifying invariants.

Invariants:
1. No overlapping intervals for same logical_id
2. At most one current version (valid_to = MAX) per logical_id
3. As-of reads return correct payload
4. Delete followed by Restore yields same logical_id with current version
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

MAX_TS = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


@dataclass
class SCDVersion:
    row_id: str
    logical_id: str
    payload: dict[str, Any]
    valid_from: datetime
    valid_to: datetime
    created_at: datetime


@dataclass
class SCDModel:
    """Pure model of SCD operations for a single table."""

    table_name: str
    logical_column: str
    versions: list[SCDVersion] = field(default_factory=list)
    _next_row_id: int = field(default=0)

    def _new_row_id(self) -> str:
        self._next_row_id += 1
        return f"row_{self._next_row_id}"

    def versions_for(self, logical_id: str) -> list[SCDVersion]:
        return [v for v in self.versions if v.logical_id == logical_id]

    def current_version(self, logical_id: str) -> SCDVersion | None:
        candidates = [v for v in self.versions_for(logical_id) if v.valid_to == MAX_TS]
        assert len(candidates) <= 1, f"Multiple current versions for {logical_id}"
        return candidates[0] if candidates else None

    def as_of(self, logical_id: str, timestamp: datetime) -> SCDVersion | None:
        candidates = [
            v for v in self.versions_for(logical_id) if v.valid_from <= timestamp < v.valid_to
        ]
        assert (
            len(candidates) == 1
        ), f"Expected exactly one version at {timestamp} for {logical_id}, found {len(candidates)}"
        return candidates[0] if candidates else None

    def assert_no_overlapping(self) -> None:
        for logical_id in {v.logical_id for v in self.versions}:
            versions = sorted(self.versions_for(logical_id), key=lambda v: v.valid_from)
            for earlier, later in zip(versions, versions[1:], strict=False):
                assert earlier.valid_to <= later.valid_from, (
                    f"Overlapping versions for {logical_id}: "
                    f"{earlier.valid_from}..{earlier.valid_to} overlaps "
                    f"{later.valid_from}..{later.valid_to}"
                )

    def assert_single_current(self) -> None:
        for logical_id in {v.logical_id for v in self.versions}:
            current = [v for v in self.versions_for(logical_id) if v.valid_to == MAX_TS]
            assert len(current) <= 1, f"Multiple current versions for {logical_id}"

    def assert_invariants(self) -> None:
        self.assert_no_overlapping()
        self.assert_single_current()


def create(model: SCDModel, logical_id: str, payload: dict[str, Any], now: datetime) -> None:
    """Create a new SCD version for a logical entity."""
    assert (
        model.current_version(logical_id) is None
    ), f"Cannot create: {logical_id} already has current version"
    model.versions.append(
        SCDVersion(
            row_id=model._new_row_id(),
            logical_id=logical_id,
            payload=dict(payload),
            valid_from=now,
            valid_to=MAX_TS,
            created_at=now,
        )
    )


def edit(model: SCDModel, logical_id: str, payload: dict[str, Any], now: datetime) -> None:
    """Edit: close current version and insert new current version."""
    current = model.current_version(logical_id)
    assert current is not None, f"Cannot edit: {logical_id} has no current version"
    current.valid_to = now
    model.versions.append(
        SCDVersion(
            row_id=model._new_row_id(),
            logical_id=logical_id,
            payload=dict(payload),
            valid_from=now,
            valid_to=MAX_TS,
            created_at=now,
        )
    )


def delete(model: SCDModel, logical_id: str, now: datetime) -> None:
    """Delete: close current version without inserting new row."""
    current = model.current_version(logical_id)
    assert current is not None, f"Cannot delete: {logical_id} has no current version"
    current.valid_to = now


def restore(model: SCDModel, logical_id: str, now: datetime) -> None:
    """Restore: find latest closed version and insert new current version."""
    assert (
        model.current_version(logical_id) is None
    ), f"Cannot restore: {logical_id} already has current version"
    closed_versions = [v for v in model.versions_for(logical_id) if v.valid_to != MAX_TS]
    assert closed_versions, f"Cannot restore: {logical_id} has no closed versions"
    latest_closed = max(closed_versions, key=lambda v: v.valid_to)
    model.versions.append(
        SCDVersion(
            row_id=model._new_row_id(),
            logical_id=logical_id,
            payload=dict(latest_closed.payload),
            valid_from=now,
            valid_to=MAX_TS,
            created_at=now,
        )
    )


# Hypothesis strategies


@st.composite
def naive_datetimes(
    draw: st.DrawFn, min_dt: datetime | None = None, max_dt: datetime | None = None
) -> datetime:
    """Generate a naive datetime and add UTC timezone."""
    min_val = min_dt or datetime(2020, 1, 1)
    max_val = max_dt or datetime(2030, 1, 1)
    naive = draw(
        st.datetimes(
            min_value=min_val,
            max_value=max_val,
        )
    )
    return naive.replace(tzinfo=timezone.utc)


@st.composite
def operation_strategy(draw: st.DrawFn) -> tuple[str, str, dict[str, Any], datetime]:
    """Generate a single operation: (op_type, logical_id, payload, now)."""
    op_type = draw(st.sampled_from(["create", "edit", "delete", "restore"]))
    logical_id = draw(st.sampled_from(["tx_1", "tx_2", "tx_3"]))
    payload = {"amount": draw(st.integers(min_value=-1000, max_value=1000))}
    now = draw(naive_datetimes())
    return op_type, logical_id, payload, now


@st.composite
def operation_sequence_strategy(draw: st.DrawFn) -> list[tuple[str, str, dict[str, Any], datetime]]:
    """Generate a sequence of operations that are valid given current state."""
    operations: list[tuple[str, str, dict[str, Any], datetime]] = []
    active_ids: set[str] = set()
    deleted_ids: set[str] = set()
    known_ids = {"tx_1", "tx_2", "tx_3"}
    current_time = datetime(2020, 1, 1, tzinfo=timezone.utc)

    for _ in range(draw(st.integers(min_value=1, max_value=10))):
        logical_id = draw(st.sampled_from(list(known_ids)))
        # Advance time by at least 1 microsecond
        delta_seconds = draw(st.integers(min_value=1, max_value=86400))
        current_time = current_time.replace(microsecond=0) + __import__("datetime").timedelta(
            seconds=delta_seconds
        )
        now = current_time
        payload = {"amount": draw(st.integers(min_value=-1000, max_value=1000))}

        if logical_id in active_ids:
            op_type = draw(st.sampled_from(["edit", "delete"]))
        elif logical_id in deleted_ids:
            op_type = "restore"
        else:
            op_type = "create"

        operations.append((op_type, logical_id, payload, now))
        if op_type == "create":
            active_ids.add(logical_id)
        elif op_type == "edit":
            pass  # stays active
        elif op_type == "delete":
            active_ids.discard(logical_id)
            deleted_ids.add(logical_id)
        elif op_type == "restore":
            active_ids.add(logical_id)
            deleted_ids.discard(logical_id)

    return operations


@settings(max_examples=50, deadline=None)
@given(operations=operation_sequence_strategy())
def test_scd_algebra_preserves_invariants(
    operations: list[tuple[str, str, dict[str, Any], datetime]],
) -> None:
    model = SCDModel(table_name="transactions", logical_column="transaction_id")
    for op_type, logical_id, payload, now in operations:
        if op_type == "create":
            create(model, logical_id, payload, now)
        elif op_type == "edit":
            edit(model, logical_id, payload, now)
        elif op_type == "delete":
            delete(model, logical_id, now)
        elif op_type == "restore":
            restore(model, logical_id, now)
        model.assert_invariants()


@settings(max_examples=20, deadline=None)
@given(
    amount_before=st.integers(min_value=-5000, max_value=-1),
    amount_after=st.integers(min_value=-5000, max_value=-1),
)
def test_edit_preserves_history(amount_before: int, amount_after: int) -> None:
    model = SCDModel(table_name="transactions", logical_column="transaction_id")
    t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

    create(model, "tx_1", {"amount": amount_before}, t1)
    as_of_before = model.as_of("tx_1", t2)
    assert as_of_before is not None
    assert as_of_before.payload["amount"] == amount_before

    edit(model, "tx_1", {"amount": amount_after}, t2)
    as_of_before_after_edit = model.as_of("tx_1", t1)
    assert as_of_before_after_edit is not None
    assert as_of_before_after_edit.payload["amount"] == amount_before

    current = model.current_version("tx_1")
    assert current is not None
    assert current.payload["amount"] == amount_after


@settings(max_examples=20, deadline=None)
@given(amount=st.integers(min_value=-5000, max_value=-1))
def test_delete_restore_preserves_transaction_id(amount: int) -> None:
    model = SCDModel(table_name="transactions", logical_column="transaction_id")
    t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 3, tzinfo=timezone.utc)

    create(model, "tx_1", {"amount": amount}, t1)
    delete(model, "tx_1", t2)
    assert model.current_version("tx_1") is None

    restore(model, "tx_1", t3)
    current = model.current_version("tx_1")
    assert current is not None
    assert current.payload["amount"] == amount
    assert current.valid_from == t3

    # Verify history: original version at t1, gap at t2..t3, restored at t3
    as_of_original = model.as_of("tx_1", t1)
    assert as_of_original is not None
    assert as_of_original.payload["amount"] == amount


@settings(max_examples=20, deadline=None)
@given(amount=st.integers(min_value=-5000, max_value=-1))
def test_restore_after_edit_preserves_latest_payload(amount: int) -> None:
    model = SCDModel(table_name="transactions", logical_column="transaction_id")
    t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)
    t3 = datetime(2026, 1, 3, tzinfo=timezone.utc)
    t4 = datetime(2026, 1, 4, tzinfo=timezone.utc)

    create(model, "tx_1", {"amount": 100}, t1)
    edit(model, "tx_1", {"amount": amount}, t2)
    delete(model, "tx_1", t3)
    restore(model, "tx_1", t4)

    current = model.current_version("tx_1")
    assert current is not None
    assert current.payload["amount"] == amount
