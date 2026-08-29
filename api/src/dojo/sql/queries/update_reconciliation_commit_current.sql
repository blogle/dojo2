UPDATE reconciliation_commits
SET state = 'CURRENT', verified_at = ?
WHERE reconciliation_id = ?
