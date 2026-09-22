INSERT INTO reconciliation_evidence_records
(evidence_id, ordinal, source_record_id, transaction_id, posted_date, cleared_date,
 signed_amount_minor, settlement_state, description, normalized_payload, raw_payload)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
