# Deployment and provisioning guide

This guide walks through provisioning dojo for a Kubernetes deployment backed by OpenEBS ZFS snapshots and encrypted Google Drive backups. It covers identity provisioning, secret management, deployment, onboarding, and backup verification.

## Prerequisites

The following tools must be available in the Nix dev shell or on the operator workstation:

- `kubectl` configured for the target cluster
- `tofu` or `terraform` (OpenTofu preferred)
- `gcloud` CLI authenticated to the Google Cloud project that will own backups
- `kubeseal` if using Bitnami Sealed Secrets
- `just` for repository commands

Enable the required Google Cloud APIs in the target project:

    gcloud services enable drive.googleapis.com iam.googleapis.com

## 1. Provision the backup service account

The OpenTofu root at `infra/opentofu/google-backup` creates the deployment-specific Google Cloud identity that will access backups. It deliberately does not create a private Drive folder, because that is owned by a human account and managed outside Google Cloud infrastructure.

Create your variable file:

    cp infra/opentofu/google-backup/terraform.tfvars.example \
       infra/opentofu/google-backup/terraform.tfvars

Edit `infra/opentofu/google-backup/terraform.tfvars` with your existing Google Cloud project ID. Commit the example but never commit your `terraform.tfvars`.

Initialize and apply:

    just drive-infra-plan
    just drive-infra-apply

Save the output:

    tofu -chdir=infra/opentofu/google-backup output -raw backup_service_account_email

This email is the identity that will receive Drive folder access. Record it alongside the project ID.

### Existing Google Sheets OAuth client

The login/import OAuth client is separate from the backup service account. It is the standard Google OAuth **Web application** client used by the Aspire Sheets import flow, with the production callback:

    https://dojo.thejeffer.net/api/onboarding/google/callback

The Google provider resource `google_iam_oauth_client` must not be used for this: it manages Workforce Identity OAuth clients, not consumer Google Sheets OAuth clients. Google does not expose the standard Credentials-console client through the Google Terraform provider. Preserve the existing client ID and secret during this migration; do not create a replacement client unless a deliberate OAuth cutover is planned.

The existing `dojo-google-oauth` Kubernetes Secret is now represented by the encrypted `SealedSecret` in `deploy/k8s/overlays/production/dojo-google-oauth-sealed.yaml`. The encrypted values are cluster-specific and cannot be decrypted outside the cluster. If the OAuth client or redirect URI changes, regenerate that SealedSecret with `kubectl get secret dojo-google-oauth -n dojo-prod -o yaml | kubeseal --format yaml` and review the diff before committing it.

## 2. Create the Drive backup folder

Create a private Google Drive folder for dojo backups. This step is performed by a human Google account owner, not Terraform.

Share the folder with the service account email from step 1 as an Editor. The folder URL contains the folder ID:

    https://drive.google.com/drive/folders/FOLDER_ID

Never use a Shared Drive folder that the service account does not have explicit access to. The folder must exist before onboarding completes.

## 3. Generate secrets

All credential material must live outside the repository and outside Terraform state. Generate each secret on a workstation with the target cluster context, then apply it directly.

### Restic password

    restic_password=$(head -c 64 /dev/urandom | base64 | head -c 64)

### Backup status token

    backup_status_token=$(head -c 64 /dev/urandom | base64 | head -c 64)

### Service account key

    gcloud iam service-accounts keys create /tmp/dojo-backup-sa.json \
      --iam-account=$(tofu -chdir=infra/opentofu/google-backup output -raw backup_service_account_email)

After applying the Secret, delete the local key file immediately:

    rm /tmp/dojo-backup-sa.json

### Apply secrets to the cluster

The examples live in `deploy/k8s/`. Apply from a temporary copy, never from the repository root.

**Restic password:**

    cat <<EOF | kubectl apply -n $NAMESPACE -f -
    apiVersion: v1
    kind: Secret
    metadata:
      name: dojo-backup-restic
    type: Opaque
    stringData:
      restic-password: "$restic_password"
    EOF

**Service account JSON:**

    kubectl create secret generic dojo-backup-google \
      --from-file=service-account.json=/tmp/dojo-backup-sa.json \
      -n $NAMESPACE \
      --dry-run=client -o yaml | kubectl apply -f -
    rm /tmp/dojo-backup-sa.json

**Backup status token:**

    cat <<EOF | kubectl apply -n $NAMESPACE -f -
    apiVersion: v1
    kind: Secret
    metadata:
      name: dojo-backup-status
    type: Opaque
    stringData:
      token: "$backup_status_token"
    EOF

**Backup configuration (ConfigMap):**

    cat <<EOF | kubectl apply -n $NAMESPACE -f -
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: dojo-backup-config
    data:
      service-account-email: "$(tofu -chdir=infra/opentofu/google-backup output -raw backup_service_account_email)"
    EOF

### Sealed Secrets alternative

If the cluster runs Bitnami Sealed Secrets, seal each manifest before applying:

    echo '{"apiVersion":"v1","kind":"Secret","metadata":{"name":"dojo-backup-restic","namespace":"'$NAMESPACE'"},"type":"Opaque","stringData":{"restic-password":"'$restic_password'"}}' \
      | kubeseal -o yaml > deploy/k8s/sealed/dojo-backup-restic.yaml

Then commit `deploy/k8s/sealed/`. The Sealed Secrets controller decrypts them at apply time. Keep the raw values and any intermediate YAML files outside the repository.

### What never enters the repository

- Service-account private keys
- Restic passwords
- Backup status tokens
- OAuth refresh tokens
- Personal Google account credentials

The checked-in `deploy/k8s/*secret.example.yaml` files are structural examples only.

## 4. Discover cluster storage classes

Before applying the production overlay, identify the cluster's OpenEBS configuration:

    kubectl get storageclass
    kubectl get volumesnapshotclass \
      -o custom-columns=NAME:.metadata.name,DRIVER:.driver,DELETION_POLICY:.deletionPolicy

Record the StorageClass name and exactly one `volumesnapshotclass` name whose driver is `zfs.csi.openebs.io`. If the cluster has more than one ZFS snapshot class, set `DOJO_VOLUME_SNAPSHOT_CLASS` on the CronJob environment.

## 5. Publish and apply

Images are built and published by GitHub Actions. Do not build or tag a local image for production. Publish a version tag through the normal repository workflow, then obtain the immutable digest from GHCR:

    docker buildx imagetools inspect ghcr.io/blogle/dojo2:<VERSION>

Set the digest from the published image on every image reference. The production overlay at `deploy/k8s/overlays/production/kustomization.yaml` pins the digest for all workload containers:

    images:
    - name: ghcr.io/blogle/dojo2
      newName: ghcr.io/blogle/dojo2
      digest: sha256:<64-hex-digest>

Apply the production overlay:

    kubectl apply -k deploy/k8s/overlays/production

Verify the rollout:

    kubectl -n $NAMESPACE rollout status deployment/dojo

## 6. Onboard the user

Open dojo in a browser. The onboarding flow will:

1. Present the choice screen.
2. After Start empty or Aspire commit, advance to backup setup.
3. Display the deployment-specific backup service-account email.
4. Ask the user to paste the Google Drive folder ID.
5. Verify the service account can write to the folder.
6. Mark backup configured and enter the application.

The folder ID is stored in the `backup_configurations` table as application data. The restic password and service-account JSON remain in Kubernetes Secrets and are never stored in DuckDB.

## 7. Initialize the restic repository

The first scheduled backup will attempt to upload to the configured Drive folder. Before that, initialize the restic repository from a workstation with rclone configured for the same service account:

    export RCLONE_CONFIG=/tmp/rclone.conf

    cat > $RCLONE_CONFIG <<EOF
    [gdrive]
    type = drive
    scope = drive
    service_account_file = /path/to/service-account.json
    root_folder_id = FOLDER_ID
    EOF

    export RESTIC_REPOSITORY=rclone:gdrive:dojo/restic
    export RESTIC_PASSWORD=/path/to/restic-password

    restic init
    rm /path/to/service-account.json

This step may be skipped if the scheduled CronJob creates the repository on first upload, but initializing explicitly prevents the first backup from failing on a missing repository.

## 8. Verify scheduled backups

Create a manual CronJob run:

    kubectl -n $NAMESPACE create job --from=cronjob/dojo-backup dojo-backup-manual
    kubectl -n $NAMESPACE wait --for=condition=complete job/dojo-backup-manual --timeout=20m
    kubectl -n $NAMESPACE logs job/dojo-backup-manual

Check that the backup reported status to the API:

    curl -s http://dojo/api/settings/backup \
      -H "Authorization: Bearer $backup_status_token_file" | jq .latest_run.status

Inspect the restic repository:

    restic snapshots

Verify the daily CronJob fires on schedule:

    kubectl -n $NAMESPACE get cronjob dojo-backup

## 9. Local Drive rehearsal

The rehearsal script proves the full upload/restore path against a unique temporary repository under `dojo-rehearsals/`. It never touches production data.

    export DOJO_GDRIVE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
    export DOJO_GDRIVE_FOLDER_ID=FOLDER_ID
    export DOJO_RESTIC_PASSWORD_FILE=/path/to/restic-password
    just drive-rehearsal

Expected output:

    Google Drive backup rehearsal passed: <snapshot-id>

The script cleans up only the rehearsal repository it created. It leaves the production repository untouched.

## 10. Restore onto a new PVC

Copy `deploy/k8s/restore-job.example.yaml`, replace every `REPLACE_*` value, and create the target PVC. The Job materializes a specific restic snapshot, verifies the backup manifest, runs migrations against the restored copy, and opens a second verification copy.

Never restore over the production PVC. Promotion requires switching the Deployment to the new PVC claim and rolling out with the same immutable image digest.

Run a restore rehearsal monthly and after any DuckDB or migration change. Record the source snapshot ID, image digests, verification output, and elapsed time.

## 11. Key rotation

To rotate the backup service account key:

1. Create a new key through `gcloud` or the Google Cloud Console.
2. Update the `dojo-backup-google` Secret.
3. Verify the scheduled backup still succeeds.
4. Delete the old key.

The restic repository password can be changed by creating a new repository and migrating snapshots. This is a manual maintenance task, not a routine operation.

## Troubleshooting

**Scheduled backup fails with "Drive access was revoked":**
Check the `dojo-backup-google` Secret contains a valid key and the Drive folder is still shared with the service account email. Run `just drive-rehearsal` to verify.

**Onboarding shows "Backup verification is not configured":**
The API container cannot read the service-account file or status token. Verify the `dojo-backup-google` and `dojo-backup-status` Secrets exist and are mounted correctly.

**Migration starts but application never becomes ready:**
Check `kubectl -n $NAMESPACE logs deployment/dojo -c migrate`. Migration is independent of Drive, so a migration failure indicates a schema issue, not a backup configuration issue.

**Restic upload fails with authentication error:**
The rclone configuration reads `service_account_file` from inside the container. Verify the Secret path matches the mount path in the CronJob Job template and the ConfigMap contains the correct service account email.
