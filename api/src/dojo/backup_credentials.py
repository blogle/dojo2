from __future__ import annotations

import base64
import binascii
import secrets
from pathlib import Path
from typing import Final
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_VERSION: Final[int] = 1
NONCE_SIZE: Final[int] = 12
KEY_SIZE: Final[int] = 32
ENVELOPE_PREFIX: Final[str] = "v1:"


class BackupCredentialError(ValueError):
    """Raised when a backup credential key or envelope is invalid."""


def load_encryption_key(path: str | Path) -> bytes:
    key_path = Path(path)
    try:
        encoded = key_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise BackupCredentialError(
            f"Credential encryption key file could not be read: {key_path}"
        ) from exc
    try:
        key = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BackupCredentialError("Credential encryption key is not valid base64") from exc
    _validate_key(key)
    return key


def _validate_key(key: bytes) -> None:
    if len(key) != KEY_SIZE:
        raise BackupCredentialError("Credential encryption key must decode to exactly 32 bytes")


def _associated_data(credential_id: UUID | str) -> bytes:
    return f"dojo:backup-google-drive:{credential_id}".encode("utf-8")


def encrypt_refresh_token(
    refresh_token: str,
    *,
    credential_id: UUID | str,
    key: bytes,
) -> str:
    _validate_key(key)
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(
        nonce, refresh_token.encode("utf-8"), _associated_data(credential_id)
    )
    return ENVELOPE_PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_refresh_token(
    envelope: str,
    *,
    credential_id: UUID | str,
    key: bytes,
) -> str:
    _validate_key(key)
    encoded = envelope.removeprefix(ENVELOPE_PREFIX)
    if encoded == envelope:
        raise BackupCredentialError("Unsupported backup credential envelope version")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BackupCredentialError("Backup credential envelope is not valid base64") from exc
    if len(payload) <= NONCE_SIZE:
        raise BackupCredentialError("Backup credential envelope is truncated")
    nonce = payload[:NONCE_SIZE]
    ciphertext = payload[NONCE_SIZE:]
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, _associated_data(credential_id))
    except InvalidTag as exc:
        raise BackupCredentialError("Backup credential authentication failed") from exc
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BackupCredentialError("Backup credential plaintext is invalid UTF-8") from exc
