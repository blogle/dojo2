ALTER TABLE backup_configurations ADD COLUMN IF NOT EXISTS google_drive_refresh_token TEXT;
DROP VIEW IF EXISTS current_backup_configurations;
CREATE OR REPLACE VIEW current_backup_configurations AS
SELECT * FROM backup_configurations
WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';
