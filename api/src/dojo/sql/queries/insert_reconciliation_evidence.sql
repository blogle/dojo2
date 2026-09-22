INSERT INTO reconciliation_evidence
(evidence_id, entity_id, entity_class, evidence_kind, source_adapter, source_as_of,
 normalized_payload, normalized_digest, created_at, created_by_user_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
