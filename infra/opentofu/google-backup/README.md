# Google Drive backup configuration

This OpenTofu root enables the Google Drive, Sheets, Picker, and API Keys APIs in an existing Google Cloud project and creates the restricted browser API key used by dojo's Google Picker. It does not create a Google service account, OAuth client, private key, human-owned Drive folder, or OAuth secret.

Authenticate with Application Default Credentials, copy `terraform.tfvars.example` to an ignored `terraform.tfvars`, set deployment-specific additional browser referrers without guessing an origin, and use the root `just drive-infra-*` commands. After apply, pass the `picker_api_key` and `picker_app_id` outputs to the API deployment configuration. Do not paste the API-key value into source control or chat.

The standard Google Auth Platform Web OAuth client remains a one-time manual bootstrap item because the normal consumer Workspace OAuth client is not represented by `google_iam_oauth_client`. Configure this client with the following local entries and keep any existing production entries:

    Authorized JavaScript origin: http://localhost:5173
    Authorized redirect URI: http://localhost:8000/api/onboarding/google/callback

The local API receives the Web OAuth client values and the API-owned credential encryption key through the normal ignored deployment secret mechanism. Backup workers never receive those values; they call dojo's internal short-lived access-token broker.
