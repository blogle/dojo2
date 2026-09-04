# Backup and restore

dojo protects production DuckDB data with OpenEBS ZFS snapshots for fast local recovery and encrypted restic snapshots in Google Drive for off-site recovery. A local snapshot is not a complete backup because it remains tied to the cluster and ZFS node.

## One-time setup

Discover the installed storage classes before deployment:

    kubectl get storageclass
    kubectl get volumesnapshotclass -o custom-columns=NAME:.metadata.name,DRIVER:.driver

The snapshot driver must be `zfs.csi.openebs.io`. The scheduled script automatically accepts exactly one matching snapshot class; set `DOJO_VOLUME_SNAPSHOT_CLASS` when the cluster has more than one. Make the production PVC's StorageClass explicit after discovery.

Create a Google service account, create a private Drive folder, and share only that folder with the service-account address. Copy `deploy/k8s/backup-secret.example.yaml` outside the repository, replace its placeholders, and apply it. Store the restic password in a separate recovery system; losing it makes every encrypted backup unusable. Initialize the repository once from a controlled workstation or Job using the same rclone configuration:

    RESTIC_REPOSITORY=rclone:gdrive:dojo/restic restic init

Before applying production manifests, replace every application image with one immutable `@sha256:` digest. The scheduled workflow refuses mutable image references because recovery must know which DuckDB runtime produced a backup.

## Scheduled backup

`dojo-backup` runs daily. Its orchestrator creates a CSI snapshot, restores that snapshot to a temporary PVC, and runs a worker using the deployed image. The worker opens the cloned database to exercise DuckDB recovery, checkpoints it, writes and verifies a SHA-256 manifest, uploads the staged directory with restic, checks repository integrity, and applies retention of 14 daily, 8 weekly, and 12 monthly snapshots. The live API remains running throughout.

Run an immediate backup with:

    just k8s-snapshot-backup

Inspect the CronJob and child Job status and alert on any failure. The workflow keeps the newest seven local snapshots and removes temporary Jobs and PVCs.

## Migration gate

The Deployment's first init container runs after the old singleton pod has stopped. If a database exists, it prepares and uploads a verified `pre-migration` restic snapshot before `dojo-migrate` can run. If Google Drive, credentials, restic verification, or database recovery fails, migration is blocked. Do not bypass this gate merely to complete a rollout; repair backup access or explicitly execute and verify an equivalent recovery copy first.

## Restore rehearsal

List snapshots with restic and choose an explicit ID rather than `latest`. Copy `deploy/k8s/restore-job.example.yaml`, replace every placeholder, and create a new empty PVC. The Job materializes the selected restic snapshot, verifies its manifest, restores it without overwriting, runs the target image's migrations, and opens a second verification copy.

Start an isolated dojo Deployment against the restored PVC. Compare `/api/app/status`, `/api/bootstrap`, representative account balances, Budget totals, Transactions, net worth, reconciliation state, and SCD2 history with recorded source values. Only after those checks pass may the production Deployment be patched to the restored claim. Keep the old PVC untouched through the rollback window.

Run this rehearsal monthly and after changing DuckDB or migration behavior. Record the restic snapshot ID, source and target image digests, verification output, elapsed restore time, and result. Never record credentials or the restic password.
