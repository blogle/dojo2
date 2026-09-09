# Google backup identity

This OpenTofu root enables the Google Drive and IAM APIs in an existing Google Cloud project and creates dojo's deployment-specific backup service account. It deliberately does not create a private key or a human-owned Drive folder: private keys would be retained in Terraform state, while personal Drive content is outside the Google Cloud provider's ownership boundary.

Authenticate with Application Default Credentials, copy `terraform.tfvars.example` to an ignored `terraform.tfvars`, then use the root `just drive-infra-*` commands. After apply, use the `backup_service_account_email` output in dojo's required backup onboarding step.

For local rehearsal, create a short-lived key with `gcloud iam service-accounts keys create` outside the repository, then revoke it after testing. Production should use workload identity where the Kubernetes platform supports it.
