#!/usr/bin/env bash
set -euo pipefail

namespace="${DOJO_NAMESPACE:-default}"
source_claim="${DOJO_DATA_CLAIM:-dojo-data}"
snapshot_class="${DOJO_VOLUME_SNAPSHOT_CLASS:-}"
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
  kubectl -n "$namespace" delete job "$job" --ignore-not-found --wait=false
  kubectl -n "$namespace" delete pvc "$clone" --ignore-not-found --wait=false
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
          /bin/dojo-backup prepare /data/dojo.duckdb /stage/dojo.duckdb --image-digest '$image' --source-snapshot '$snapshot'
          restic backup /stage --tag dojo --tag scheduled --tag '$snapshot'
          restic check
          restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 12 --prune
        env:
        - name: RESTIC_REPOSITORY
          value: rclone:gdrive:dojo/restic
        - name: RESTIC_PASSWORD_FILE
          value: /backup-secrets/restic-password
        - name: RCLONE_CONFIG
          value: /backup-secrets/rclone.conf
        volumeMounts:
        - name: data
          mountPath: /data
        - name: stage
          mountPath: /stage
        - name: backup-secrets
          mountPath: /backup-secrets
          readOnly: true
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: $clone
      - name: stage
        emptyDir: {}
      - name: backup-secrets
        secret:
          secretName: dojo-backup-credentials
EOF

kubectl -n "$namespace" wait --for=condition=complete "job/$job" --timeout=20m

# Local snapshots are only the fast recovery layer. Keep the newest seven.
mapfile -t old_snapshots < <(
  kubectl -n "$namespace" get volumesnapshot -l dojo.backup/kind=scheduled \
    --sort-by=.metadata.creationTimestamp -o name | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d' | sed '$d'
)
if [[ "${#old_snapshots[@]}" -gt 0 ]]; then
  kubectl -n "$namespace" delete "${old_snapshots[@]}"
fi
