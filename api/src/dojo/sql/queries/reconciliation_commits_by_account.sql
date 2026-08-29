SELECT * FROM reconciliation_commits
WHERE account_id = ?
ORDER BY effective_date DESC, created_at DESC
