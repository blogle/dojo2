SELECT *
FROM backup_runs
WHERE status <> 'SKIPPED'
ORDER BY updated_at DESC, backup_run_id DESC
LIMIT 1
