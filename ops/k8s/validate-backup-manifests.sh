#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

DOJO_BUILD_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
DOJO_BACKUP_JOB_NAME=dojo-backup-test \
DOJO_BACKUP_RUN_ID=00000000-0000-4000-8000-000000000001 \
DOJO_BACKUP_SNAPSHOT=dojo-data-test \
DOJO_BACKUP_CLONE=dojo-backup-test \
  DOJO_BACKUP_STATUS_URL=http://dojo \
  "$repo_root/ops/k8s/snapshot-backup.sh" --render-job \
  | yq eval '.' - >/dev/null

yq eval '.' "$repo_root/deploy/k8s/restore-job.example.yaml" >/dev/null

rbac="$repo_root/deploy/k8s/base/backup-rbac.yaml"
yq eval -e 'select(.kind == "Role" and .metadata.name == "dojo-backup") | .rules[] | select(.apiGroups == ["coordination.k8s.io"] and .resources == ["leases"] and .resourceNames == ["dojo-backup-global"] and (.verbs | contains(["get", "update"])))' "$rbac" >/dev/null
yq eval -e 'select(.kind == "Role" and .metadata.name == "dojo-backup") | .rules[] | select(.apiGroups == ["coordination.k8s.io"] and .resources == ["leases"] and .resourceNames == null and (.verbs | contains(["create"])))' "$rbac" >/dev/null
if yq eval -e 'select(.kind == "Role" and .metadata.name == "dojo-backup-trigger") | .rules[] | select((.apiGroups | contains(["coordination.k8s.io"])) and (.resources | contains(["leases"])))' "$rbac" >/dev/null; then
  printf 'The backup-trigger Role must not have Lease permissions.\n' >&2
  exit 1
fi

deployment="$repo_root/deploy/k8s/base/deployment.yaml"
yq eval -e 'select(.kind == "Deployment" and .metadata.name == "dojo") | .spec.template.spec.automountServiceAccountToken == false' "$deployment" >/dev/null
yq eval -e 'select(.kind == "Deployment" and .metadata.name == "dojo") | [.spec.template.spec.containers[] | select(.name == "dojo") | .volumeMounts[]? | select(.name == "backup-trigger-kubernetes")] | length == 0' "$deployment" >/dev/null

printf 'Backup and restore Kubernetes manifests are valid.\n'
