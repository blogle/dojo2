INSERT INTO reconciliation_source_records
(source_evidence_id, source_record_id, transaction_id, ordinal, account_id, posted_date,
 cleared_date, signed_amount_minor, source_status, description,
 normalized_digest, raw_payload)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
