SELECT *
FROM reconciliation_commits
WHERE entity_id = ?
ORDER BY committed_at DESC, reconciliation_id DESC
