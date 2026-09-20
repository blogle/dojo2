#!/usr/bin/env bash
set -euo pipefail

namespace="${DOJO_NAMESPACE:-default}"
source_claim="${DOJO_DATA_CLAIM:-dojo-data}"
snapshot_class="${DOJO_VOLUME_SNAPSHOT_CLASS:-}"
trigger_kind="${DOJO_BACKUP_TRIGGER_KIND:-SCHEDULED}"
backup_kind="${trigger_kind,,}"

render_job() {
  : "${DOJO_BACKUP_JOB_NAME:?Set DOJO_BACKUP_JOB_NAME}"
  : "${DOJO_BACKUP_RUN_ID:?Set DOJO_BACKUP_RUN_ID}"
  : "${DOJO_BACKUP_SNAPSHOT:?Set DOJO_BACKUP_SNAPSHOT}"
  : "${DOJO_BACKUP_IMAGE:?Set DOJO_BACKUP_IMAGE}"
  : "${DOJO_BACKUP_CLONE:?Set DOJO_BACKUP_CLONE}"
  cat <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: ${DOJO_BACKUP_JOB_NAME}
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: backup
        image: ${DOJO_BACKUP_IMAGE}
        command: [/bin/bash, -euc]
        args:
        - |
          set -euo pipefail
          /bin/dojo-backup-status --url '${DOJO_BACKUP_STATUS_URL:-http://dojo}' --token-file /backup-status/token --run-id '${DOJO_BACKUP_RUN_ID}' --trigger-kind '${trigger_kind}' --status RUNNING --phase PREPARING --source-snapshot '${DOJO_BACKUP_SNAPSHOT}' --image-digest '${DOJO_BACKUP_IMAGE}' || true
          /bin/dojo-backup prepare /data/dojo.duckdb /stage/dojo.duckdb --image-digest '${DOJO_BACKUP_IMAGE}' --source-snapshot '${DOJO_BACKUP_SNAPSHOT}'
          snapshot_id="\$(/bin/dojo-backup-upload upload --staging-directory /stage --internal-api-url http://dojo --internal-token-file /backup-status/token --restic-password-file /restic/restic-password --repository-path dojo/restic --tag dojo --tag '${backup_kind}' --tag '${DOJO_BACKUP_SNAPSHOT}' --retain)"
          database_sha256="\$(python -c 'import json; print(json.load(open("/stage/dojo.duckdb.manifest.json"))["database_sha256"])')"
          database_size="\$(python -c 'import json; print(json.load(open("/stage/dojo.duckdb.manifest.json"))["database_size"])')"
          /bin/dojo-backup-status --url '${DOJO_BACKUP_STATUS_URL:-http://dojo}' --token-file /backup-status/token --run-id '${DOJO_BACKUP_RUN_ID}' --trigger-kind '${trigger_kind}' --status SUCCEEDED --phase COMPLETE --source-snapshot '${DOJO_BACKUP_SNAPSHOT}' --image-digest '${DOJO_BACKUP_IMAGE}' --restic-snapshot-id "\$snapshot_id" --database-sha256 "\$database_sha256" --database-size-bytes "\$database_size" || true
        env:
        - name: RESTIC_REPOSITORY
          value: rclone:gdrive:dojo/restic
        - name: RESTIC_PASSWORD_FILE
          value: /restic/restic-password
        volumeMounts:
        - name: data
          mountPath: /data
        - name: stage
          mountPath: /stage
        - name: restic
          mountPath: /restic
          readOnly: true
        - name: backup-status
          mountPath: /backup-status
          readOnly: true
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ${DOJO_BACKUP_CLONE}
      - name: stage
        emptyDir: {}
      - name: restic
        secret:
          secretName: dojo-backup-restic
      - name: backup-status
        secret:
          secretName: dojo-backup-status
      - name: tmp
        emptyDir: {}
EOF
}

if [[ "${1:-}" == "--render-job" ]]; then
  render_job
  exit 0
fi
run_id="${DOJO_BACKUP_RUN_ID:-$(python -c 'from uuid import uuid4; print(uuid4())')}"
phase="STARTING"
snapshot=""
image=""
failure_message=""

report_status() {
  [[ -f "${DOJO_BACKUP_STATUS_TOKEN_FILE:-}" ]] || return 0
  args=(
    --url "${DOJO_BACKUP_STATUS_URL:-http://dojo}"
    --token-file "${DOJO_BACKUP_STATUS_TOKEN_FILE}"
    --run-id "$run_id"
    --trigger-kind "$trigger_kind"
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
    report_status FAILED "$phase" "${failure_message:-Backup failed during ${phase}.}"
  fi
  kubectl -n "$namespace" delete job "$job" --ignore-not-found --wait=true
  kubectl -n "$namespace" delete pvc "$clone" --ignore-not-found --wait=true
  exit "$result"
}
trap cleanup EXIT

wait_for_backup_job() {
  for _ in $(seq 1 1200); do
    complete="$(kubectl -n "$namespace" get job "$job" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}')"
    [[ "$complete" == "True" ]] && return 0

    failed="$(kubectl -n "$namespace" get job "$job" -o jsonpath='{.status.conditions[?(@.type=="Failed")].status}')"
    if [[ "$failed" == "True" ]]; then
      failure_message="$(kubectl -n "$namespace" get job "$job" -o jsonpath='{.status.conditions[?(@.type=="Failed")].message}')"
      if [[ -z "$failure_message" ]]; then
        failure_message="$(kubectl -n "$namespace" logs "job/$job" -c backup --tail=50 2>&1 || true)"
        failure_message="${failure_message//$'\n'/ }"
        failure_message="${failure_message:0:900}"
        [[ -n "$failure_message" ]] && failure_message="Backup worker failed: $failure_message"
      fi
      [[ -n "$failure_message" ]] || failure_message="Backup worker failed without a diagnostic."
      return 1
    fi
    sleep 1
  done

  failure_message="Backup timed out waiting for the backup worker to complete."
  return 1
}

kubectl -n "$namespace" apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: $snapshot
  labels:
    app: dojo
    dojo.backup/kind: $backup_kind
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
EOF
DOJO_BACKUP_JOB_NAME="$job" \
DOJO_BACKUP_RUN_ID="$run_id" \
DOJO_BACKUP_SNAPSHOT="$snapshot" \
DOJO_BACKUP_IMAGE="$image" \
DOJO_BACKUP_CLONE="$clone" \
DOJO_BACKUP_STATUS_URL="${DOJO_BACKUP_STATUS_URL:-http://dojo}" \
  render_job | kubectl -n "$namespace" apply -f -

phase="VERIFYING"
wait_for_backup_job
report_status SUCCEEDED COMPLETE ""

# Local snapshots are only the fast recovery layer. Keep the newest seven.
mapfile -t old_snapshots < <(
  kubectl -n "$namespace" get volumesnapshot -l dojo.backup/kind=scheduled \
    --sort-by=.metadata.creationTimestamp -o name | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d'
)
if [[ "${#old_snapshots[@]}" -gt 0 ]]; then
  kubectl -n "$namespace" delete "${old_snapshots[@]}"
fi
