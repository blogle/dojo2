BEGIN TRANSACTION;
CREATE TABLE backup_runs_dojo35 (
    backup_run_id UUID PRIMARY KEY,
    trigger_kind TEXT NOT NULL,
    status TEXT NOT NULL,
    phase TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL,
    source_snapshot TEXT,
    image_digest TEXT,
    restic_snapshot_id TEXT,
    database_sha256 TEXT,
    database_size_bytes BIGINT,
    error_message TEXT,
    CHECK (trigger_kind IN ('SCHEDULED', 'MANUAL')),
    CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED', 'SKIPPED')),
    CHECK (database_size_bytes IS NULL OR database_size_bytes >= 0)
);
INSERT INTO backup_runs_dojo35 SELECT * FROM backup_runs;
DROP TABLE backup_runs;
ALTER TABLE backup_runs_dojo35 RENAME TO backup_runs;
COMMIT;
