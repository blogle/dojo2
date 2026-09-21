"""Pure account-local reconciliation comparison and digest functions."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

import duckdb

from dojo.database import Database, json_dumps
from dojo.sql import load_sql

SUPPORTED_ENTITY_CLASSES = frozenset({"BUDGET", "INVESTMENT", "LOAN", "TRACKING", "TANGIBLE_ASSET"})


@dataclass(frozen=True)
class LocalRecord:
    transaction_id: str
    valid_from: str
    account_id: str
    posted_date: date
    signed_amount_minor: int
    status: str
    category_id: str | None
    system_category: str | None
    memo: str
    source_record_id: str | None = None


@dataclass(frozen=True)
class SourceRecord:
    source_record_id: str
    posted_date: date
    signed_amount_minor: int
    status: str
    description: str = ""
    cleared_date: date | None = None
    transaction_id: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedEvidence:
    """Provider-neutral evidence that can be reconstructed without its adapter."""

    entity_id: str
    entity_class: str
    evidence_kind: str
    source_adapter: str
    source_as_of: datetime
    normalized_payload: Mapping[str, Any]
    records: tuple[Mapping[str, Any], ...] = ()
    evidence_id: str = field(default_factory=lambda: str(uuid4()))


class ReconciliationRepository:
    """Shared persistence boundary for immutable reconciliation history."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create_commit(
        self,
        *,
        entity_id: str,
        entity_class: str,
        evidence: NormalizedEvidence | Mapping[str, Any],
        committed_at: datetime,
        baseline_digest: str | None = None,
        baseline_refs: Sequence[Mapping[str, Any]] = (),
        reconciliation_id: str | None = None,
        created_by_user_id: str | None = None,
        connection: duckdb.DuckDBPyConnection | None = None,
    ) -> dict[str, Any]:
        normalized_entity_id = str(entity_id)
        self._validate_entity_class(entity_class)
        committed_at = _require_aware_datetime(committed_at, "committed_at")
        normalized_evidence = self._normalize_evidence(
            evidence,
            entity_id=normalized_entity_id,
            entity_class=entity_class,
        )
        refs = tuple(dict(ref) for ref in baseline_refs)
        self._validate_baseline_refs(refs, normalized_entity_id)
        commit_id = reconciliation_id or str(uuid4())
        digest = baseline_digest or _baseline_reference_digest(refs)

        if connection is not None:
            return self._create_commit(
                connection,
                normalized_entity_id,
                entity_class,
                normalized_evidence,
                committed_at,
                digest,
                refs,
                commit_id,
                created_by_user_id,
            )
        with self.database.transaction() as transaction:
            return self._create_commit(
                transaction,
                normalized_entity_id,
                entity_class,
                normalized_evidence,
                committed_at,
                digest,
                refs,
                commit_id,
                created_by_user_id,
            )

    def read_evidence(self, evidence_id: str) -> dict[str, Any]:
        row = self.database.fetch_one(
            load_sql("queries/reconciliation_evidence_by_id"), (evidence_id,)
        )
        if row is None:
            raise ValueError("Reconciliation evidence not found")
        return self._evidence_result(
            row,
            self.database.fetch_all(
                load_sql("queries/reconciliation_evidence_records_by_id"), (evidence_id,)
            ),
        )

    def read_commit(self, reconciliation_id: str) -> dict[str, Any]:
        row = self.database.fetch_one(
            load_sql("queries/reconciliation_commit_by_id"), (reconciliation_id,)
        )
        if row is None:
            raise ValueError("Reconciliation commit not found")
        evidence = self.read_evidence(str(row["evidence_id"]))
        return row | {"source_as_of": evidence["source_as_of"], "evidence": evidence}

    def list_commits(self, entity_id: str) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            load_sql("queries/reconciliation_commits_by_entity"), (entity_id,)
        )

    def list_history(self, entity_id: str) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            load_sql("queries/reconciliation_history_by_entity"), (entity_id,)
        )

    def void_commit(
        self,
        *,
        reconciliation_id: str,
        entity_id: str,
        entity_class: str,
        recorded_at: datetime,
        reason: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._validate_entity_class(entity_class)
        recorded_at = _require_aware_datetime(recorded_at, "recorded_at")
        with self.database.transaction() as connection:
            commit_cursor = connection.execute(
                load_sql("queries/reconciliation_commit_by_id"), (reconciliation_id,)
            )
            commit_row = _cursor_row(commit_cursor)
            if commit_row is None:
                raise ValueError("Reconciliation commit not found")
            if str(commit_row["entity_id"]) != str(entity_id):
                raise ValueError("Reconciliation commit entity does not match the void record")
            if str(commit_row["entity_class"]) != entity_class:
                raise ValueError(
                    "Reconciliation commit entity class does not match the void record"
                )
            history_id = str(uuid4())
            connection.execute(
                load_sql("queries/insert_reconciliation_history"),
                (
                    history_id,
                    entity_id,
                    entity_class,
                    "VOID",
                    reconciliation_id,
                    recorded_at,
                    reason,
                    json_dumps(metadata) if metadata is not None else None,
                ),
            )
        return {
            "history_id": history_id,
            "entity_id": str(entity_id),
            "entity_class": entity_class,
            "event_type": "VOID",
            "reconciliation_id": reconciliation_id,
            "recorded_at": recorded_at,
            "reason": reason,
        }

    def _create_commit(
        self,
        connection: duckdb.DuckDBPyConnection,
        entity_id: str,
        entity_class: str,
        evidence: NormalizedEvidence,
        committed_at: datetime,
        baseline_digest: str,
        baseline_refs: tuple[dict[str, Any], ...],
        commit_id: str,
        created_by_user_id: str | None,
    ) -> dict[str, Any]:
        existing_evidence = _cursor_row(
            connection.execute(
                load_sql("queries/reconciliation_evidence_by_id"), (evidence.evidence_id,)
            )
        )
        if existing_evidence is None:
            connection.execute(
                load_sql("queries/insert_reconciliation_evidence"),
                (
                    evidence.evidence_id,
                    entity_id,
                    entity_class,
                    evidence.evidence_kind,
                    evidence.source_adapter,
                    evidence.source_as_of,
                    json_dumps(dict(evidence.normalized_payload)),
                    _evidence_digest(evidence),
                    committed_at,
                    created_by_user_id,
                ),
            )
            for ordinal, record in enumerate(evidence.records):
                connection.execute(
                    load_sql("queries/insert_reconciliation_evidence_record"),
                    _record_parameters(evidence.evidence_id, ordinal, record),
                )
        elif (
            str(existing_evidence["entity_id"]) != entity_id
            or str(existing_evidence["entity_class"]) != entity_class
            or str(existing_evidence["evidence_kind"]) != evidence.evidence_kind
            or str(existing_evidence["source_adapter"]) != evidence.source_adapter
            or existing_evidence["source_as_of"] != evidence.source_as_of
            or str(existing_evidence["normalized_digest"]) != _evidence_digest(evidence)
        ):
            raise ValueError("Evidence linkage or immutable metadata does not match the commit")

        connection.execute(
            load_sql("queries/insert_reconciliation_commit"),
            (
                commit_id,
                entity_id,
                entity_class,
                evidence.evidence_id,
                baseline_digest,
                committed_at,
                created_by_user_id,
            ),
        )
        history_id = str(uuid4())
        connection.execute(
            load_sql("queries/insert_reconciliation_history"),
            (
                history_id,
                entity_id,
                entity_class,
                "COMMITTED",
                commit_id,
                committed_at,
                None,
                None,
            ),
        )
        for ref in baseline_refs:
            connection.execute(
                load_sql("queries/insert_reconciliation_transaction_ref"),
                (
                    commit_id,
                    ref["transaction_id"],
                    ref["valid_from"],
                    ref.get("account_id", entity_id),
                    ref.get("canonical_row_digest", ""),
                ),
            )
        return {
            "reconciliation_id": commit_id,
            "entity_id": entity_id,
            "entity_class": entity_class,
            "evidence_id": evidence.evidence_id,
            "baseline_digest": baseline_digest,
            "committed_at": committed_at,
            "source_as_of": evidence.source_as_of,
            "history_id": history_id,
            "evidence": {
                "evidence_id": evidence.evidence_id,
                "entity_id": entity_id,
                "entity_class": entity_class,
                "evidence_kind": evidence.evidence_kind,
                "source_adapter": evidence.source_adapter,
                "source_as_of": evidence.source_as_of,
                "normalized_payload": dict(evidence.normalized_payload),
                "normalized_digest": _evidence_digest(evidence),
                "records": [dict(record) for record in evidence.records],
            },
        }

    @staticmethod
    def _validate_entity_class(entity_class: str) -> None:
        if entity_class not in SUPPORTED_ENTITY_CLASSES:
            raise ValueError(f"Unsupported reconciliation entity class: {entity_class}")

    def _normalize_evidence(
        self,
        evidence: NormalizedEvidence | Mapping[str, Any],
        *,
        entity_id: str,
        entity_class: str,
    ) -> NormalizedEvidence:
        if isinstance(evidence, NormalizedEvidence):
            normalized = evidence
        else:
            evidence_entity_id = str(evidence.get("entity_id", entity_id))
            evidence_entity_class = str(evidence.get("entity_class", entity_class))
            payload = evidence.get("normalized_payload", evidence.get("payload", {}))
            records = evidence.get("records", ())
            if (
                not isinstance(payload, Mapping)
                or not isinstance(records, Sequence)
                or isinstance(records, (str, bytes, bytearray))
                or not all(isinstance(record, Mapping) for record in records)
            ):
                raise ValueError("Normalized evidence payload and records must be structured")
            normalized = NormalizedEvidence(
                entity_id=evidence_entity_id,
                entity_class=evidence_entity_class,
                evidence_kind=str(evidence["evidence_kind"]),
                source_adapter=str(evidence["source_adapter"]),
                source_as_of=_require_aware_datetime(evidence["source_as_of"], "source_as_of"),
                normalized_payload=payload,
                records=tuple(records),
                evidence_id=str(evidence.get("evidence_id") or uuid4()),
            )
        if normalized.entity_id != entity_id or normalized.entity_class != entity_class:
            raise ValueError("Evidence entity linkage does not match the reconciliation commit")
        self._validate_entity_class(normalized.entity_class)
        return replace(
            normalized,
            source_as_of=_require_aware_datetime(normalized.source_as_of, "source_as_of"),
        )

    @staticmethod
    def _validate_baseline_refs(refs: tuple[dict[str, Any], ...], entity_id: str) -> None:
        for ref in refs:
            if not {"transaction_id", "valid_from"} <= ref.keys():
                raise ValueError("Baseline references require transaction_id and valid_from")
            if ref.get("account_id", entity_id) != entity_id:
                raise ValueError(
                    "Baseline reference account does not match the reconciliation entity"
                )

    @staticmethod
    def _evidence_result(row: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
        payload = row["normalized_payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        normalized_records = []
        for record in records:
            record_payload = record["normalized_payload"]
            if isinstance(record_payload, str):
                record_payload = json.loads(record_payload)
            normalized_records.append(record | {"normalized_payload": record_payload})
        return row | {"normalized_payload": payload, "records": normalized_records}


def _cursor_row(cursor: duckdb.DuckDBPyConnection) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if row is None or cursor.description is None:
        return None
    return dict(zip([column[0] for column in cursor.description], row, strict=True))


def _require_aware_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _record_parameters(
    evidence_id: str, ordinal: int, record: Mapping[str, Any]
) -> tuple[Any, ...]:
    payload = record.get("normalized_payload", dict(record))
    if not isinstance(payload, Mapping):
        raise ValueError("Normalized evidence records must be structured")
    return (
        evidence_id,
        ordinal,
        str(record["source_record_id"]) if record.get("source_record_id") is not None else None,
        str(record["transaction_id"]) if record.get("transaction_id") is not None else None,
        _date_value(record.get("posted_date")),
        _date_value(record.get("cleared_date")),
        record.get("signed_amount_minor"),
        record.get("settlement_state", record.get("source_status")),
        str(record.get("description", "")),
        json_dumps(dict(payload)),
        json_dumps(record.get("raw_payload")) if record.get("raw_payload") is not None else None,
    )


def _date_value(value: Any) -> date | None:
    if isinstance(value, str):
        return date.fromisoformat(value)
    if value is None or isinstance(value, date):
        return value
    raise ValueError("Normalized evidence dates must be ISO dates")


def _evidence_digest(evidence: NormalizedEvidence) -> str:
    return sha256(
        json_dumps(
            {
                "payload": dict(evidence.normalized_payload),
                "records": [dict(record) for record in evidence.records],
            }
        ).encode("utf-8")
    ).hexdigest()


def _baseline_reference_digest(refs: Sequence[Mapping[str, Any]]) -> str:
    return sha256(json_dumps([dict(ref) for ref in refs]).encode("utf-8")).hexdigest()


def canonical_transaction(record: LocalRecord) -> str:
    value = {
        "account_id": record.account_id,
        "amount_minor": record.signed_amount_minor,
        "category_id": record.category_id,
        "date": record.posted_date.isoformat(),
        "memo": record.memo,
        "status": record.status,
        "system_category": record.system_category,
        "transaction_id": record.transaction_id,
        "valid_from": record.valid_from,
    }
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def transaction_digest(record: LocalRecord) -> str:
    return sha256(canonical_transaction(record).encode("utf-8")).hexdigest()


def source_digest(record: SourceRecord) -> str:
    value = {
        "amount_minor": record.signed_amount_minor,
        "cleared_date": record.cleared_date.isoformat() if record.cleared_date else None,
        "date": record.posted_date.isoformat(),
        "description": record.description,
        "source_record_id": record.source_record_id,
        "status": record.status,
    }
    return sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def baseline_digest(
    records: list[LocalRecord],
    *,
    account_id: str,
    cutoff: date,
    source_evidence_id: str,
    source_evidence_digest: str,
    settings_versions: list[str] | None = None,
) -> str:
    payload = {
        "account_id": account_id,
        "cutoff": cutoff.isoformat(),
        "records": sorted(transaction_digest(record) for record in records),
        "settings_versions": sorted(settings_versions or []),
        "source_evidence_digest": source_evidence_digest,
        "source_evidence_id": source_evidence_id,
    }
    return sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def compare_records(
    local_records: list[LocalRecord], source_records: list[SourceRecord]
) -> dict[str, Any]:
    """Classify only explicit identities; descriptions and amounts are not identity."""
    local_by_id = {
        record.source_record_id: record for record in local_records if record.source_record_id
    }
    matched_local: set[str] = set()
    exact: list[dict[str, str]] = []
    mismatches: list[dict[str, Any]] = []
    source_only: list[dict[str, Any]] = []
    duplicate_ids: set[str] = set()
    seen_source_ids: set[str] = set()

    for source in source_records:
        if source.source_record_id in seen_source_ids:
            duplicate_ids.add(source.source_record_id)
        seen_source_ids.add(source.source_record_id)
        local = local_by_id.get(source.source_record_id)
        if local is None and source.transaction_id:
            local = next(
                (item for item in local_records if item.transaction_id == source.transaction_id),
                None,
            )
        if local is None:
            source_only.append({"source_record_id": source.source_record_id})
            continue
        matched_local.add(local.transaction_id)
        fields = {
            name: (getattr(local, local_name), getattr(source, source_name))
            for name, local_name, source_name in (
                ("date", "posted_date", "posted_date"),
                ("amount", "signed_amount_minor", "signed_amount_minor"),
                ("status", "status", "status"),
            )
        }
        changed = [name for name, (left, right) in fields.items() if left != right]
        if changed:
            mismatches.append({"source_record_id": source.source_record_id, "fields": changed})
        else:
            exact.append(
                {
                    "source_record_id": source.source_record_id,
                    "transaction_id": local.transaction_id,
                }
            )

    local_only = [
        {"transaction_id": record.transaction_id}
        for record in local_records
        if record.transaction_id not in matched_local
    ]
    return {
        "exact_matches": exact,
        "source_only": source_only,
        "local_only": local_only,
        "duplicates": [{"source_record_id": value} for value in sorted(duplicate_ids)],
        "mismatches": mismatches,
    }
