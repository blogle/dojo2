"""Pure account-local reconciliation comparison and digest functions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Any


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
