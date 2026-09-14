#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
api_url="${DOJO_API_URL:-http://localhost:8000}"
: "${BACKUP_STATUS_TOKEN_FILE:?Set BACKUP_STATUS_TOKEN_FILE}"
: "${DOJO_RESTIC_PASSWORD_FILE:?Set DOJO_RESTIC_PASSWORD_FILE}"

[[ -f "$BACKUP_STATUS_TOKEN_FILE" ]] || {
  printf 'Required file does not exist: %s\n' "$BACKUP_STATUS_TOKEN_FILE" >&2
  exit 1
}
[[ -f "$DOJO_RESTIC_PASSWORD_FILE" ]] || {
  printf 'Required file does not exist: %s\n' "$DOJO_RESTIC_PASSWORD_FILE" >&2
  exit 1
}
BACKUP_STATUS_TOKEN_FILE="$(realpath "$BACKUP_STATUS_TOKEN_FILE")"
DOJO_RESTIC_PASSWORD_FILE="$(realpath "$DOJO_RESTIC_PASSWORD_FILE")"

(
  cd "$repo_root/api"
  uv run python -c '
import httpx
import sys

url = sys.argv[1].rstrip("/") + "/health"
try:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
except Exception as exc:
    raise SystemExit(f"A running dojo API is required at {url}: {exc}") from exc
' "$api_url"
)

run_id="$(python -c 'from uuid import uuid4; print(uuid4().hex)')"
remote_path="dojo-rehearsals/$run_id/restic"
[[ "$remote_path" != "dojo/restic" ]] || {
  printf 'Refusing to use the production repository.\n' >&2
  exit 1
}

work="$(mktemp -d -t dojo-drive-rehearsal.XXXXXX)"
chmod 700 "$work"
remote_created=0

cleanup() {
  result=$?
  set +e
  if [[ "$remote_created" -eq 1 ]]; then
    (
      cd "$repo_root/api"
      uv run python -m dojo.drive_uploader purge \
        --internal-api-url "$api_url" \
        --internal-token-file "$BACKUP_STATUS_TOKEN_FILE" \
        --repository-path "$remote_path"
    ) >/dev/null 2>&1 || true
  fi
  rm -rf "$work"
  exit "$result"
}
trap cleanup EXIT

(
  cd "$repo_root/api"
  uv run python -m dojo.migrations "$work/source.duckdb"
  uv run python -m dojo.backup prepare \
    "$work/source.duckdb" \
    "$work/stage/dojo.duckdb" \
    --image-digest local-rehearsal \
    --source-snapshot "$run_id"
)

remote_created=1
snapshot_id="$(
  cd "$repo_root/api"
  uv run python -m dojo.drive_uploader upload \
    --staging-directory "$work/stage" \
    --internal-api-url "$api_url" \
    --internal-token-file "$BACKUP_STATUS_TOKEN_FILE" \
    --restic-password-file "$DOJO_RESTIC_PASSWORD_FILE" \
    --repository-path "$remote_path" \
    --tag dojo-drive-rehearsal
)"

(
  cd "$repo_root/api"
  uv run python -m dojo.drive_uploader restore \
    --snapshot-id "$snapshot_id" \
    --target-directory "$work/materialized" \
    --internal-api-url "$api_url" \
    --internal-token-file "$BACKUP_STATUS_TOKEN_FILE" \
    --restic-password-file "$DOJO_RESTIC_PASSWORD_FILE" \
    --repository-path "$remote_path"
  restored_manifest="$(find "$work/materialized" -type f -name '*.manifest.json' -print -quit)"
  [[ -n "$restored_manifest" ]] || {
    printf 'Restored backup manifest was not found.\n' >&2
    exit 1
  }
  restored_database="${restored_manifest%.manifest.json}"
  [[ -f "$restored_database" ]] || {
    printf 'Restored backup database was not found.\n' >&2
    exit 1
  }
  uv run python -m dojo.backup verify \
    "$restored_database" \
    "$restored_manifest"
  uv run python -m dojo.backup restore \
    "$restored_database" \
    "$restored_manifest" \
    "$work/restored.duckdb"
  uv run python -m dojo.migrations "$work/restored.duckdb"
)

printf 'Google Drive backup rehearsal passed: %s\n' "$snapshot_id"
