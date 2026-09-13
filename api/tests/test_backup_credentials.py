from __future__ import annotations

import base64
from pathlib import Path

import duckdb
import pytest

from dojo.backup_credentials import (
    BackupCredentialError,
    decrypt_refresh_token,
    encrypt_refresh_token,
    load_encryption_key,
)
from dojo.constants import SYSTEM_BACKUP_CREDENTIAL_ID
from dojo.migrations import apply_migrations, provision_database

KEY = b"0123456789abcdef0123456789abcdef"
CREDENTIAL_ID = SYSTEM_BACKUP_CREDENTIAL_ID


def test_load_encryption_key(tmp_path: Path) -> None:
    key_path = tmp_path / "credential-key"
    key_path.write_text(base64.b64encode(KEY).decode("ascii"), encoding="utf-8")

    assert load_encryption_key(key_path) == KEY


@pytest.mark.parametrize(
    ("filename", "contents", "message"),
    [
        ("missing", None, "could not be read"),
        ("malformed", "not-base64!", "not valid base64"),
        ("wrong-size", base64.b64encode(b"short").decode("ascii"), "exactly 32 bytes"),
    ],
)
def test_load_encryption_key_rejects_invalid_files(
    tmp_path: Path, filename: str, contents: str | None, message: str
) -> None:
    key_path = tmp_path / filename
    if contents is not None:
        key_path.write_text(contents, encoding="utf-8")

    with pytest.raises(BackupCredentialError, match=message):
        load_encryption_key(key_path)


def test_encrypt_decrypt_round_trip_and_random_nonce() -> None:
    first = encrypt_refresh_token("opaque-test-value", credential_id=CREDENTIAL_ID, key=KEY)
    second = encrypt_refresh_token("opaque-test-value", credential_id=CREDENTIAL_ID, key=KEY)

    assert first != second
    assert decrypt_refresh_token(first, credential_id=CREDENTIAL_ID, key=KEY) == "opaque-test-value"


def test_decrypt_rejects_wrong_identity_and_key() -> None:
    envelope = encrypt_refresh_token("opaque-test-value", credential_id=CREDENTIAL_ID, key=KEY)
    wrong_key = b"fedcba9876543210fedcba9876543210"

    with pytest.raises(BackupCredentialError, match="authentication failed"):
        decrypt_refresh_token(envelope, credential_id="other", key=KEY)
    with pytest.raises(BackupCredentialError, match="authentication failed"):
        decrypt_refresh_token(envelope, credential_id=CREDENTIAL_ID, key=wrong_key)


def test_fresh_schema_has_encrypted_credentials_without_plaintext_column(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "fresh.duckdb"
    provision_database(str(duckdb_path))
    connection = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        backup_columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'backup_configurations'"
            ).fetchall()
        }
        credential_columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'backup_credentials'"
            ).fetchall()
        }
    finally:
        connection.close()

    assert "google_drive_refresh_token" not in backup_columns
    assert {
        "credential_id",
        "encrypted_refresh_token",
        "granted_scopes",
        "key_version",
        "created_at",
        "updated_at",
    } == credential_columns


def test_compatibility_repair_drops_plaintext_and_preserves_configuration(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "legacy.duckdb"
    provision_database(str(duckdb_path))
    connection = duckdb.connect(str(duckdb_path))
    try:
        connection.execute("DROP VIEW current_backup_configurations")
        connection.execute(
            "ALTER TABLE backup_configurations ADD COLUMN google_drive_refresh_token TEXT"
        )
        connection.execute(
            """
            INSERT INTO backup_configurations (
                row_id, configuration_id, status, drive_folder_id, drive_folder_name,
                credential_id, verified_at, last_error, valid_from, valid_to,
                created_at, created_by_user_id, google_drive_refresh_token
            ) VALUES (
                '00000000-0000-4000-8000-000000000001',
                '00000000-0000-0000-0000-00000000ba01', 'CONFIGURED', 'folder-a',
                'Folder A', NULL, TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL,
                TIMESTAMPTZ '2026-01-01 00:00:00+00', TIMESTAMPTZ '9999-12-31 23:59:59+00',
                TIMESTAMPTZ '2026-01-01 00:00:00+00', NULL, 'legacy-secret-placeholder'
            )
            """
        )
        apply_migrations(connection)
        connection.execute("DROP VIEW current_backup_configurations")
        columns = {
            row[0]
            for row in connection.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'backup_configurations'"
            ).fetchall()
        }
        row = connection.execute(
            "SELECT status, drive_folder_id, drive_folder_name, last_error "
            "FROM backup_configurations"
        ).fetchone()
    finally:
        connection.close()

    assert "google_drive_refresh_token" not in columns
    assert row == ("CONFIGURED", "folder-a", "Folder A", None)
