# Deployment and provisioning guide

This guide provisions dojo with OpenEBS ZFS snapshots and user-authorized, encrypted Google Drive backups.

## Prerequisites

- `kubectl` configured for the target cluster
- `tofu` or `terraform` (OpenTofu preferred)
- `gcloud` authenticated to the target Google Cloud project
- `kubeseal` when using Sealed Secrets
- `just` in the repository dev shell

## 1. Provision Google project services

The OpenTofu root at `infra/opentofu/google-backup` manages the Drive, Sheets, Picker, and API Keys services, a restricted Picker browser key, and the numeric project-number output. It does not manage a consumer OAuth client or a Drive folder.

Create an untracked variable file from the example, set only the target project, then run:

    just drive-infra-plan
    just drive-infra-apply

The standard Google Auth Platform Web OAuth client is a manual bootstrap. Configure the consent screen, authorized origins and redirect URI for the deployment, and provide its client ID and secret through the `dojo-google-oauth` deployment secret. Do not put client values in this repository or Terraform state. The OAuth consent screen must be verified before external users use the Aspire migration scope.

## 2. Configure cluster secrets

The API deployment needs the Web OAuth client, Picker API key and project number, the backup-status token, and the AES-256-GCM credential-encryption master key. The backup worker needs only its staged database data, restic password, status token, and internal broker access. Do not mount refresh tokens, encryption keys, OAuth client secrets, or service-account files into the worker.

Keep the restic password and master key in the deployment's secret-management system. Keep their raw values and generated manifests outside the repository. The API reads the master key from the configured key-file path and stores the Google refresh token encrypted in `backup_credentials`.

## 3. Discover storage and deploy

    kubectl get storageclass
    kubectl get volumesnapshotclass \
      -o custom-columns=NAME:.metadata.name,DRIVER:.driver,DELETION_POLICY:.deletionPolicy

Use a class with driver `zfs.csi.openebs.io`; set `DOJO_VOLUME_SNAPSHOT_CLASS` if more than one matches. Pin every production image to an immutable `sha256:` digest, apply the production overlay, and verify its rollout:

    kubectl apply -k deploy/k8s/overlays/production
    kubectl -n "$NAMESPACE" rollout status deployment/dojo

## 4. Onboard and configure Drive

Open dojo in a browser. Start empty requests Drive file access only. Aspire migration requests Sheets read access and Drive file access in one combined OAuth grant. After authorization, choose a folder with Google Picker. The API verifies the selected folder with direct Drive metadata and a zero-byte create/delete probe, then stores its canonical ID and name with the credential identity. No folder ID is pasted, and no service-account sharing is required.

An existing ready workspace remains usable when credentials are missing or the latest backup failed. Its warning links to `/onboarding?backup=repair`; repair reauthorizes Drive when needed and repeats folder selection.

## 5. Verify scheduled backups

    kubectl -n "$NAMESPACE" create job --from=cronjob/dojo-backup dojo-backup-manual
    kubectl -n "$NAMESPACE" wait --for=condition=complete job/dojo-backup-manual --timeout=20m
    kubectl -n "$NAMESPACE" logs job/dojo-backup-manual

The Kubernetes boundary owns the VolumeSnapshot, temporary PVC, child Job, status reporting, and cleanup. The worker requests a short-lived access token from the authenticated API broker and calls the shared uploader. It never refreshes Google credentials itself.

## 6. Local rehearsal

The opt-in rehearsal uses the same uploader and broker as Kubernetes. It requires a healthy local API already configured with an encrypted credential and verified folder, plus local-only files for the restic password and backup-status token. Set `DOJO_RESTIC_PASSWORD_FILE` and `BACKUP_STATUS_TOKEN_FILE` to those local file paths, then run:

    just drive-rehearsal

It creates a unique temporary `dojo-rehearsals/` repository, verifies and restores a snapshot into a separate local target, and cleans up only that rehearsal repository. It must not use `kubectl` or modify `dojo/restic`; it is excluded from CI because it requires explicit live-Drive approval and network access.

## 7. Restore

Use `deploy/k8s/restore-job.example.yaml` with a new empty PVC and an explicit snapshot ID. The Job verifies the manifest, runs migrations, and opens a second verification copy. Never restore over the production PVC. Promote only after comparing application status, balances, budgets, transactions, net worth, reconciliation state, and SCD2 history.

## Troubleshooting

**Backup is degraded:** Check the API's backup status and use the Repair backups action. Do not inspect or copy refresh tokens; reauthorize through the standard Web OAuth flow.

**Folder setup fails:** Confirm the API has a valid encrypted credential, Picker settings, and network access to Drive. Folder verification is a direct metadata and write/delete probe, not an rclone request handler operation.

**Migration or API startup fails:** Drive is outside migration and readiness. Inspect migration logs and database provisioning independently.

**Worker upload authentication fails:** The short-lived broker token may have expired or the durable API credential may be revoked. Retry after repair; do not add a refresh token or service-account file to the worker.
