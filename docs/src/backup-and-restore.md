# Backup and restore

dojo protects production DuckDB data with OpenEBS ZFS snapshots for fast local recovery and encrypted restic snapshots in Google Drive for off-site recovery. A local snapshot is not a complete backup because it remains tied to the cluster and ZFS node.

## One-time setup

See the [Deployment and provisioning guide](deployment-provisioning.md) for the complete provisioning sequence. The summary:

Discover the installed storage classes before deployment:

    kubectl get storageclass
    kubectl get volumesnapshotclass -o custom-columns=NAME:.metadata.name,DRIVER:.driver

The snapshot driver must be `zfs.csi.openebs.io`. The scheduled script automatically accepts exactly one matching snapshot class; set `DOJO_VOLUME_SNAPSHOT_CLASS` when the cluster has more than one. Make the production PVC's StorageClass explicit after discovery.

Use `infra/opentofu/google-backup` to enable the Drive API and create the deployment-specific service account in an existing Google Cloud project:

    just drive-infra-plan
    just drive-infra-apply

Copy the `backup_service_account_email` output. The user then creates a private Drive folder and shares only that folder with that email. The verified folder ID is stored as deployment data during dojo onboarding; no human Google identity is stored in the repository or application database.

Apply separate Secrets and ConfigMap using the checked-in examples:

    deploy/k8s/backup-config.example.yaml
    deploy/k8s/backup-secret.example.yaml   # Google service-account JSON
    deploy/k8s/restic-secret.example.yaml    # restic password
    deploy/k8s/backup-status-secret.example.yaml

Store the restic password in a separate recovery system; losing it makes every encrypted backup unusable. Initialize the repository once from a controlled workstation or Job using the same rclone configuration:

    RESTIC_REPOSITORY=rclone:gdrive:dojo/restic restic init

Before applying production manifests, replace every application image with one immutable `@sha256:` digest. The scheduled workflow refuses mutable image references because recovery must know which DuckDB runtime produced a backup.

## Scheduled backup

`dojo-backup` runs daily. Its orchestrator creates a CSI snapshot, restores that snapshot to a temporary PVC, and runs a worker using the deployed image. The worker opens the cloned database to exercise DuckDB recovery, checkpoints it, writes and verifies a SHA-256 manifest, uploads the staged directory with restic, checks repository integrity, and applies retention of 14 daily, 8 weekly, and 12 monthly snapshots. The live API remains running throughout.

Run an immediate backup with:

    just k8s-snapshot-backup

Inspect the CronJob and child Job status and alert on any failure. The workflow keeps the newest seven local snapshots and removes temporary Jobs and PVCs.

## Migration independence

`dojo-migrate` does not access Google Drive and does not mount backup credentials. A Drive outage, missing Secret, or revoked folder permission cannot block migration or API startup. Scheduled backup failures are reported to the internal status endpoint and shown as a persistent warning. OpenEBS snapshots remain the local recovery layer.

## Restore rehearsal

List snapshots with restic and choose an explicit ID rather than `latest`. Copy `deploy/k8s/restore-job.example.yaml`, replace every placeholder, and create a new empty PVC. The Job materializes the selected restic snapshot, verifies its manifest, restores it without overwriting, runs the target image's migrations, and opens a second verification copy.

Start an isolated dojo Deployment against the restored PVC. Compare `/api/app/status`, `/api/bootstrap`, representative account balances, Budget totals, Transactions, net worth, reconciliation state, and SCD2 history with recorded source values. Only after those checks pass may the production Deployment be patched to the restored claim. Keep the old PVC untouched through the rollback window.

Run this rehearsal monthly and after changing DuckDB or migration behavior. Record the restic snapshot ID, source and target image digests, verification output, elapsed restore time, and result. Never record credentials or the restic password.

## Local Drive rehearsal

Set environment variables for the backup service-account JSON, Drive folder ID, and restic password file, then run the opt-in rehearsal:

    export DOJO_GDRIVE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
    export DOJO_GDRIVE_FOLDER_ID=your-folder-id
    export DOJO_RESTIC_PASSWORD_FILE=/path/to/restic-password
    just drive-rehearsal

The script creates a unique temporary restic repository beneath `dojo-rehearsals`, uploads a generated DuckDB backup, verifies and restores the exact snapshot, reruns migrations, and removes only that rehearsal repository. This command is intentionally excluded from CI because it requires live Google credentials and network access.
