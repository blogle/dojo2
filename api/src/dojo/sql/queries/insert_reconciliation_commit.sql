INSERT INTO reconciliation_commits
(reconciliation_id, account_id, account_class, source_kind, period_start,
 period_end, effective_date, verified_at, state, source_evidence_id,
 source_evidence_digest, baseline_digest, source_ending_value_minor,
 created_at, created_by_user_id)
VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'DRAFT', ?, ?, ?, ?, ?, NULL)
