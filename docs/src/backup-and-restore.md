# Backup and restore

dojo combines OpenEBS ZFS snapshots for fast local recovery with encrypted restic snapshots in Google Drive for off-site recovery. A local snapshot remains tied to the cluster and ZFS node.

## Setup

Use [Deployment and provisioning](deployment-provisioning.md) for project services, the manually bootstrapped standard Web OAuth client, deployment secrets, and storage discovery. OpenTofu manages the restricted Picker API key and project number, not a consumer OAuth client or Drive identity.

New users authorize through OAuth: Start empty requests Drive file access only; Aspire migration uses one combined Sheets-read and Drive-file grant. The browser selects a folder with Google Picker. The API verifies it directly with metadata and a zero-byte write/delete probe.

The API stores the refresh token in an AES-256-GCM encrypted credential row. Kubernetes and local workers receive only a short-lived access token from the authenticated broker. No refresh token, master key, OAuth client secret, or service-account identity crosses that boundary.

## Scheduled backup

`dojo-backup` creates a CSI snapshot, clones it to a temporary PVC, prepares and verifies a DuckDB manifest, and invokes the shared platform-neutral uploader. The worker checks the restic repository and applies retention. Kubernetes owns snapshot and temporary-resource lifecycle; the live API and migration remain independent of Drive.

Run an immediate backup with:

    just k8s-snapshot-backup

Later failures or missing durable credentials leave an existing ready workspace usable and produce a persistent warning. Use Repair backups to reauthorize or reconfigure the folder.

## Restore rehearsal

Choose an explicit restic snapshot ID, restore to a new PVC using `deploy/k8s/restore-job.example.yaml`, verify the manifest, run migrations, and compare representative application state before promotion. Never overwrite the production PVC. Record snapshot ID, immutable image digests, verification output, elapsed time, and result, but never credentials or passwords.

## Local Drive rehearsal

The local rehearsal is deliberately opt-in and local-only in its prerequisites. Configure a healthy local API with an encrypted Google credential and verified folder, provide local files through `DOJO_RESTIC_PASSWORD_FILE` and `BACKUP_STATUS_TOKEN_FILE`, then run:

    just drive-rehearsal

It uses the same broker and uploader as Kubernetes, creates a unique temporary repository beneath `dojo-rehearsals`, restores to a separate target, verifies the result, and removes only that rehearsal repository. It does not use `kubectl`, touch `dojo/restic`, or run in CI; live Google access requires explicit approval.
