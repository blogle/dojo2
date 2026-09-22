SELECT *
FROM reconciliation_history
WHERE entity_id = ?
ORDER BY recorded_at DESC, history_id DESC
