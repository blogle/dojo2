SELECT credential_id, encrypted_refresh_token, granted_scopes, key_version, created_at, updated_at
FROM backup_credentials
WHERE credential_id = ?
