#!/usr/bin/env bash
set -euo pipefail

: "${DOJO_GDRIVE_SERVICE_ACCOUNT_FILE:?Set DOJO_GDRIVE_SERVICE_ACCOUNT_FILE}"
: "${DOJO_GDRIVE_FOLDER_ID:?Set DOJO_GDRIVE_FOLDER_ID}"
: "${DOJO_RESTIC_PASSWORD_FILE:?Set DOJO_RESTIC_PASSWORD_FILE}"

for path in "$DOJO_GDRIVE_SERVICE_ACCOUNT_FILE" "$DOJO_RESTIC_PASSWORD_FILE"; do
  [[ -f "$path" ]] || { printf 'Required file does not exist: %s\n' "$path" >&2; exit 1; }
done

run_id="$(date -u +%Y%m%d%H%M%S)-$(python -c 'from uuid import uuid4; print(str(uuid4())[:8])')"
remote_path="dojo-rehearsals/$run_id"
work="$(mktemp -d -t dojo-drive-rehearsal.XXXXXX)"
chmod 700 "$work"

cleanup() {
  result=$?
  set +e
  if [[ "$remote_path" == dojo-rehearsals/* ]]; then
    RCLONE_CONFIG="$work/rclone.conf" rclone purge "gdrive:$remote_path"
  fi
  rm -rf "$work"
  exit "$result"
}
trap cleanup EXIT

cat > "$work/rclone.conf" <<EOF
[gdrive]
type = drive
scope = drive
service_account_file = $DOJO_GDRIVE_SERVICE_ACCOUNT_FILE
root_folder_id = $DOJO_GDRIVE_FOLDER_ID
EOF
chmod 600 "$work/rclone.conf"

export RCLONE_CONFIG="$work/rclone.conf"
export RESTIC_PASSWORD_FILE="$DOJO_RESTIC_PASSWORD_FILE"
export RESTIC_REPOSITORY="rclone:gdrive:$remote_path/restic"

probe_name=".dojo-storage-probe-$run_id"
probe_remote="gdrive:$remote_path/$probe_name"
printf 'ok' | rclone rcat "$probe_remote"
rclone delete "$probe_remote"

(cd api && uv run python -m dojo.migrations "$work/source.duckdb")
(cd api && uv run python -m dojo.backup prepare "$work/source.duckdb" "$work/stage/dojo.duckdb" --image-digest local-rehearsal --source-snapshot "$run_id")
restic init
restic backup "$work/stage" --tag dojo-drive-rehearsal --json > "$work/restic-result.json"
restic check
snapshot_id="$(python -c 'import json,sys; rows=[json.loads(line) for line in open(sys.argv[1])]; print(next(row["snapshot_id"] for row in reversed(rows) if row.get("message_type") == "summary"))' "$work/restic-result.json")"
restic restore "$snapshot_id" --target "$work/materialized"
(cd api && uv run python -m dojo.backup verify "$work/materialized$work/stage/dojo.duckdb" "$work/materialized$work/stage/dojo.duckdb.manifest.json")
(cd api && uv run python -m dojo.backup restore "$work/materialized$work/stage/dojo.duckdb" "$work/materialized$work/stage/dojo.duckdb.manifest.json" "$work/restored.duckdb")
(cd api && uv run python -m dojo.migrations "$work/restored.duckdb")
printf 'Google Drive backup rehearsal passed: %s\n' "$snapshot_id"
