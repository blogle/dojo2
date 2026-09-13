INSERT INTO backup_credentials (
    credential_id,
    encrypted_refresh_token,
    granted_scopes,
    key_version,
    created_at,
    updated_at
)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (credential_id) DO UPDATE SET
    encrypted_refresh_token = excluded.encrypted_refresh_token,
    granted_scopes = excluded.granted_scopes,
    key_version = excluded.key_version,
    updated_at = excluded.updated_at
