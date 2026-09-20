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

printf 'Backup and restore Kubernetes manifests are valid.\n'
