INSERT INTO backup_runs (
    backup_run_id, trigger_kind, status, phase, started_at, completed_at,
    updated_at, source_snapshot, image_digest, restic_snapshot_id,
    database_sha256, database_size_bytes, error_message
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (backup_run_id) DO UPDATE SET
    status = excluded.status,
    phase = excluded.phase,
    completed_at = excluded.completed_at,
    updated_at = excluded.updated_at,
    source_snapshot = COALESCE(excluded.source_snapshot, backup_runs.source_snapshot),
    image_digest = COALESCE(excluded.image_digest, backup_runs.image_digest),
    restic_snapshot_id = COALESCE(excluded.restic_snapshot_id, backup_runs.restic_snapshot_id),
    database_sha256 = COALESCE(excluded.database_sha256, backup_runs.database_sha256),
    database_size_bytes = COALESCE(excluded.database_size_bytes, backup_runs.database_size_bytes),
    error_message = excluded.error_message
