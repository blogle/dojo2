INSERT INTO backup_runs (
    backup_run_id, trigger_kind, status, phase, started_at, completed_at,
    updated_at, source_snapshot, image_digest, restic_snapshot_id,
    database_sha256, database_size_bytes, error_message
) VALUES (?, 'MANUAL', 'RUNNING', 'QUEUED', ?, NULL, ?, NULL, NULL, NULL, NULL, NULL, NULL)
