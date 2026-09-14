DROP VIEW IF EXISTS current_backup_configurations;
ALTER TABLE backup_configurations ADD COLUMN IF NOT EXISTS drive_folder_name TEXT;
ALTER TABLE backup_configurations ADD COLUMN IF NOT EXISTS credential_id UUID;
ALTER TABLE backup_configurations DROP COLUMN IF EXISTS google_drive_refresh_token;
CREATE TABLE IF NOT EXISTS backup_credentials (
    credential_id UUID PRIMARY KEY,
    encrypted_refresh_token TEXT NOT NULL,
    granted_scopes TEXT NOT NULL,
    key_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE OR REPLACE VIEW current_backup_configurations AS
SELECT * FROM backup_configurations
WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';
