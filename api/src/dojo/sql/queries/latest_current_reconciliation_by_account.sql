SELECT * FROM reconciliation_commits
WHERE account_id = ? AND state = 'CURRENT'
ORDER BY effective_date DESC, created_at DESC
LIMIT 1
