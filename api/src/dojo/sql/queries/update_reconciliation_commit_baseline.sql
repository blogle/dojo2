UPDATE reconciliation_commits
SET state = 'CURRENT', verified_at = ?, baseline_digest = ?
WHERE reconciliation_id = ?
