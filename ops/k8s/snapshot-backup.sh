#!/usr/bin/env bash
set -euo pipefail

namespace="${DOJO_NAMESPACE:-default}"
source_claim="${DOJO_DATA_CLAIM:-dojo-data}"
snapshot_class="${DOJO_VOLUME_SNAPSHOT_CLASS:-}"
run_id="$(python -c 'from uuid import uuid4; print(uuid4())')"
phase="STARTING"
snapshot=""
image=""

report_status() {
  [[ -f "${DOJO_BACKUP_STATUS_TOKEN_FILE:-}" ]] || return 0
  args=(
    --url "${DOJO_BACKUP_STATUS_URL}"
    --token-file "${DOJO_BACKUP_STATUS_TOKEN_FILE}"
    --run-id "$run_id"
    --trigger-kind SCHEDULED
    --status "$1"
    --phase "$2"
  )
  [[ -n "$snapshot" ]] && args+=(--source-snapshot "$snapshot")
  [[ -n "$image" ]] && args+=(--image-digest "$image")
  [[ -n "${3:-}" ]] && args+=(--error-message "$3")
  /bin/dojo-backup-status "${args[@]}" >/dev/null 2>&1 || true
}

report_status RUNNING STARTING ""
if [[ -z "$snapshot_class" ]]; then
  mapfile -t snapshot_classes < <(
    kubectl get volumesnapshotclass \
      -o jsonpath='{range .items[?(@.driver=="zfs.csi.openebs.io")]}{.metadata.name}{"\n"}{end}'
  )
  if [[ "${#snapshot_classes[@]}" -ne 1 ]]; then
    printf 'Expected exactly one OpenEBS ZFS VolumeSnapshotClass; found %s\n' "${#snapshot_classes[@]}" >&2
    exit 1
  fi
  snapshot_class="${snapshot_classes[0]}"
fi

storage_class="$(kubectl -n "$namespace" get pvc "$source_claim" -o jsonpath='{.spec.storageClassName}')"
image="$(kubectl -n "$namespace" get deployment dojo -o jsonpath='{.spec.template.spec.containers[?(@.name=="dojo")].image}')"
if [[ "$image" != *@sha256:* ]]; then
  printf 'Scheduled backups require an immutable deployment image digest, got %s\n' "$image" >&2
  exit 1
fi

stamp="$(date -u +%Y%m%d%H%M%S)"
snapshot="dojo-data-$stamp"
clone="dojo-backup-$stamp"
job="dojo-backup-$stamp"

cleanup() {
  result=$?
  set +e
  if [[ "$result" -ne 0 ]]; then
    report_status FAILED "$phase" "Scheduled backup failed during ${phase}."
  fi
  kubectl -n "$namespace" delete job "$job" --ignore-not-found --wait=true
  kubectl -n "$namespace" delete pvc "$clone" --ignore-not-found --wait=true
  exit "$result"
}
trap cleanup EXIT

kubectl -n "$namespace" apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: $snapshot
  labels:
    app: dojo
    dojo.backup/kind: scheduled
spec:
  volumeSnapshotClassName: $snapshot_class
  source:
    persistentVolumeClaimName: $source_claim
EOF
phase="SNAPSHOTTING"
report_status RUNNING "$phase" ""

for _ in $(seq 1 120); do
  [[ "$(kubectl -n "$namespace" get volumesnapshot "$snapshot" -o jsonpath='{.status.readyToUse}')" == "true" ]] && break
  sleep 2
done
[[ "$(kubectl -n "$namespace" get volumesnapshot "$snapshot" -o jsonpath='{.status.readyToUse}')" == "true" ]]

kubectl -n "$namespace" apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $clone
spec:
  storageClassName: $storage_class
  dataSource:
    name: $snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: batch/v1
kind: Job
metadata:
  name: $job
spec:
  backoffLimit: 1
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: backup
        image: $image
        command: [/bin/bash, -cu]
        args:
        - |
          export RCLONE_CONFIG_GDRIVE_ROOT_FOLDER_ID="$(python -c 'import httpx; payload=httpx.get("http://dojo/api/settings/backup", timeout=10).json(); print(payload["configuration"]["folder_id"])')"
          /bin/dojo-backup-status --url '${DOJO_BACKUP_STATUS_URL}' --token-file /backup-status/token --run-id '$run_id' --trigger-kind SCHEDULED --status RUNNING --phase PREPARING --source-snapshot '$snapshot' --image-digest '$image' || true
          /bin/dojo-backup prepare /data/dojo.duckdb /stage/dojo.duckdb --image-digest '$image' --source-snapshot '$snapshot'
          restic backup /stage --tag dojo --tag scheduled --tag '$snapshot' --json > /stage/restic-result.json
          restic check
          restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 12 --prune
          snapshot_id="$(python -c 'import json; from pathlib import Path; rows=[json.loads(line) for line in Path("/stage/restic-result.json").read_text().splitlines()]; print(next(row["snapshot_id"] for row in reversed(rows) if row.get("message_type") == "summary"))')"
          database_sha256="$(python -c 'import json; print(json.load(open("/stage/dojo.duckdb.manifest.json"))["database_sha256"])')"
          database_size="$(python -c 'import json; print(json.load(open("/stage/dojo.duckdb.manifest.json"))["database_size"])')"
          /bin/dojo-backup-status --url '${DOJO_BACKUP_STATUS_URL}' --token-file /backup-status/token --run-id '$run_id' --trigger-kind SCHEDULED --status SUCCEEDED --phase COMPLETE --source-snapshot '$snapshot' --image-digest '$image' --restic-snapshot-id "$snapshot_id" --database-sha256 "$database_sha256" --database-size-bytes "$database_size" || true
        env:
        - name: RESTIC_REPOSITORY
          value: rclone:gdrive:dojo/restic
        - name: RESTIC_PASSWORD_FILE
          value: /restic/restic-password
        - name: RCLONE_CONFIG
          value: /google-backup/rclone.conf
        volumeMounts:
        - name: data
          mountPath: /data
        - name: stage
          mountPath: /stage
        - name: google-backup
          mountPath: /google-backup
          readOnly: true
        - name: restic
          mountPath: /restic
          readOnly: true
        - name: backup-status
          mountPath: /backup-status
          readOnly: true
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: $clone
      - name: stage
        emptyDir: {}
      - name: google-backup
        secret:
          secretName: dojo-backup-google
      - name: restic
        secret:
          secretName: dojo-backup-restic
      - name: backup-status
        secret:
          secretName: dojo-backup-status
EOF

phase="VERIFYING"
kubectl -n "$namespace" wait --for=condition=complete "job/$job" --timeout=20m
report_status SUCCEEDED COMPLETE ""

# Local snapshots are only the fast recovery layer. Keep the newest seven.
mapfile -t old_snapshots < <(
  kubectl -n "$namespace" get volumesnapshot -l dojo.backup/kind=scheduled \
    --sort-by=.metadata.creationTimestamp -o name | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d'
)
if [[ "${#old_snapshots[@]}" -gt 0 ]]; then
  kubectl -n "$namespace" delete "${old_snapshots[@]}"
fi
