# Implement user-OAuth Google Drive backups

This is a living ExecPlan for replacing dojo's inconsistent Google Drive backup identity with one user-authorized Google OAuth flow for each purpose. It must remain sufficiently complete for a stateless contributor to resume the work from this file alone. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` are updated at every stopping point.

## Purpose / Big Picture

After this change, a new dojo user can start empty or migrate from Aspire and configure encrypted Google Drive backups without sharing a folder with a service account or pasting a folder ID. Aspire migration requests Sheets read access and Drive file access in one OAuth grant; Start empty requests Drive file access only. The browser chooses a folder through Google's Picker, while the API verifies the selected folder by writing and deleting a zero-byte probe through the Google Drive HTTP API.

An already-onboarded workspace remains usable when its new durable credential is absent, invalid, or its latest backup failed. The existing global warning takes the user to `/onboarding?backup=repair`. The API owns the encrypted Google refresh token and the encryption key. Kubernetes backup workers receive only a short-lived Google access token from the authenticated internal broker, then use the same platform-neutral uploader as the local rehearsal. No refresh token, encryption key, OAuth client secret, or service-account backup identity is placed in a backup worker or commit.

The complete local proof consists of deterministic tests, fresh and upgraded DuckDB provisioning, rendered Kubernetes and OpenTofu validation, human Start-empty/Aspire/repair browser gates, and an explicitly approved real Google Drive backup-and-restore rehearsal. Nothing is pushed until all local gates and human gates pass.

## Progress

- [x] (2026-09-12) Confirmed `/workspace/dojo2` is the mounted project, read the root guidance, the required product and architecture documents, and `.agents/skills/execplan/SKILL.md`.
- [x] (2026-09-12) Confirmed the initial worktree was clean on `master` and created local branch `feat/google-drive-user-oauth-backups`.
- [x] (2026-09-12) Ran `direnv allow` and `just setup`.
- [x] (2026-09-12) Repaired only the ignored API virtual environment after discovering stale host-path launchers; no tracked dependency change was made.
- [x] (2026-09-12) Applied the user-authorized formatting-only baseline repair to `api/src/dojo/drive_backup.py` and `api/tests/test_api_endpoints.py`.
- [x] (2026-09-12) Applied the smallest baseline type correction in `api/src/dojo/drive_backup.py` so the current `mypy` version accepts the existing JSON return.
- [x] (2026-09-12) Confirmed the full `just check` passes under a temporary `Xvfb` display. The ordinary headless invocation cannot start Cypress because no `DISPLAY` exists.
- [x] (2026-09-12) Created and committed only this ExecPlan as `6fc8248` with `docs: plan user OAuth Google Drive backups`.
- [x] (2026-09-12) Implemented encrypted credential persistence and the plaintext-column compatibility repair; `just migration-check`, `just test-unit`, `just test-integration`, `just architecture-check`, `just typecheck`, and `just lint` pass.
- [x] (2026-09-12) Split OAuth by explicit purpose and persist refresh credentials immediately; 97 unit tests, 81 integration tests, migration-check, architecture-check, typecheck, and lint pass.
- [x] (2026-09-12) Implemented direct Drive verification, Picker session configuration, browser Picker adapter, and backup setup UI; 98 unit tests, 81 integration tests, web tests, typecheck, lint, and web build pass.
- [x] (2026-09-12) Implemented the internal short-lived credential broker and one platform-neutral uploader; removed worker credential-file access; 105 unit tests, 85 integration tests, architecture-check, typecheck, lint, and k8s-render pass.
- [x] (2026-09-12) Rewrote the local rehearsal to use the shared uploader; 108 unit tests, 85 integration tests, lint, and typecheck pass.
- [x] (2026-09-12) Completed legacy readiness and repair behavior with integration and web tests; 111 unit tests, 88 integration tests, 45 web unit tests, 275 Cypress component tests, migration-check, typecheck, and lint pass.
- [x] (2026-09-12) Replaced OpenTofu service-account resources with project services and a restricted Picker API key; removed active Kubernetes service-account backup dependencies; infrastructure formatting/validation and k8s-render pass.
- [ ] Stop at Human Gate A, run `just drive-infra-plan`, and wait for explicit approval before applying infrastructure.
- [ ] Stop at Human Gate B and wait for confirmation that the standard Web OAuth client has the local origin and redirect without removing existing production entries.
- [ ] Prepare local environment documentation and safe ignored-file placeholders without creating or displaying credentials.
- [ ] Stop at Human Gates C, D, E, and F for real local Start-empty, Aspire, repair, and Drive rehearsal validation; record each result here.
- [ ] Align current documentation and commit it.
- [ ] Run final `just check`, `just ci`, infrastructure checks, manifest rendering, searches, and diff review; update this plan and commit any final plan outcome.
- [ ] Stop at Human Gate G and ask: `Local implementation and validation are complete. Do you want me to push the feature branch and open the PR?`
- [ ] Only after approval, push the feature branch, open a PR against `master`, wait for green CI, and stop at Human Gate H before merge or staging promotion.
- [ ] Only after promotion approval, use the existing merge and staging workflow. Production is out of scope.

## Surprises & Discoveries

- Observation: The first `just check` stopped at formatting in `api/src/dojo/drive_backup.py` and `api/tests/test_api_endpoints.py`.
  Evidence: `just format` changed only those two tracked files; the user authorized that formatting-only repair.
- Observation: The initial API virtual environment contained `mypy`, but its launcher pointed to `/home/ogle/src/dojo2/api/.venv/bin/python`, which is outside this mounted workspace.
  Evidence: `api/.venv/bin/mypy` had that shebang. `uv sync --reinstall` repaired the ignored environment without changing tracked files.
- Observation: The current code had one `mypy` error after the environment was repaired.
  Evidence: `drive_backup.py:29` returned `Any` from `_refresh_access_token`; a `typing.cast(str, ...)` is the minimal baseline correction.
- Observation: Cypress component tests require a display server even though the repository's Nix shell supplies Cypress.
  Evidence: Without a display, Cypress reported missing `$DISPLAY` and X server initialization failure. Running the unchanged `just check` with temporary `Xvfb :99` passed all 275 component tests.
- Observation: The current backup identity is internally split: onboarding writes a refresh token to DuckDB, but the Kubernetes worker reads a different refresh token file from `Secret/dojo-backup-google`.
  Evidence: `DojoService.configure_backup_folder()` persists `google_drive_refresh_token`, while `ops/k8s/snapshot-backup.sh` reads `/google-backup/refresh-token`; no synchronization path exists.
- Observation: Fresh schema provisioning currently adds the plaintext token through a compatibility migration rather than defining it in `current.sql`.
  Evidence: `api/src/dojo/sql/schema/migrations/add_backup_oauth_token.sql` adds the nullable column after `current.sql` runs. The replacement must define the new credential table in the fresh schema and make the old repair remove the column.
- Observation: The OpenTofu root has no consumer OAuth client resource and must not gain one.
  Evidence: The requested standard consumer Web OAuth client is not represented by `google_iam_oauth_client`; only project services, a restricted API key, and the project-number output belong in this root.
- Observation: Running `uv add` outside the repository's pinned Nix environment rewrote unrelated lockfile metadata, while the existing lock already contained cryptography transitively through Authlib.
  Evidence: The newer inherited `uv` added upload-time metadata across 703 lines. Restoring the generated lock content and adding only dojo-api's direct dependency entries left the intended package change without unrelated resolver churn.
- Observation: The existing `just test-unit` did not include `tests/test_google.py`, even though that module owns the OAuth unit coverage.
  Evidence: The Phase 2 command now includes it, producing 97 passing unit tests and making scope/pending-state regressions part of the canonical unit gate.
- Observation: Direct Drive probe cleanup needs to retain the created file ID before any later response parsing or error handling.
  Evidence: `verify_drive_folder()` keeps the probe ID and performs deletion in `finally`, so a failed delete is surfaced while every created probe receives a cleanup attempt.
- Observation: The repository architecture policy also forbids direct wall-clock calls in the shared uploader.
  Evidence: The initial uploader used a token expiry timestamp and failed `architecture-check`; omitting expiry from the access-token-only rclone config keeps the worker from refreshing and satisfies the short-lived-token boundary.
- Observation: The existing `just test-unit` and `just test-integration` lists require explicit updates for new broker/uploader tests.
  Evidence: The Phase 4 recipes now include `test_backup_access.py` and `test_drive_uploader.py`; the gates report 105 and 85 passing tests respectively.
- Observation: Rehearsal cleanup needs the same broker-backed ephemeral configuration as upload and restore because the uploader removes its config after each operation.
  Evidence: `purge_repository()` obtains a fresh short-lived token, purges only a `dojo-rehearsals/` path, and deletes its temporary config; the shell trap invokes it on both success and failure.
- Observation: A successful latest backup must not make a ready workspace appear healthy when the durable credential has been removed by the compatibility repair.
  Evidence: `get_app_status()` now requires both a successful latest run and an existing encrypted credential for `backup.state = configured`; otherwise a ready workspace remains degraded.
- Observation: Vue Router navigation from the existing warning is asynchronous in the Vitest environment.
  Evidence: The repair-warning regression test requires `flushPromises()` after clicking Repair backups before asserting `/onboarding?backup=repair`.
- Observation: The Google provider exposes a `google_apikeys_key` value as `key_string`, not `key`.
  Evidence: The first `drive-infra-validate` failed on `google_apikeys_key.picker.key`; changing the output to `key_string` made validation pass.
- Observation: The base Kubernetes deployment has no checked-in overlay for deployment-specific Web OAuth, Picker, and encryption secrets.
  Evidence: The rendered base manifest references `dojo-google-oauth`, `dojo-google-picker`, and `dojo-backup-credentials` by secret key, leaving their values to the deployment environment without inventing an origin or credential.

## Decision Log

- Decision: Use one fixed system credential row identified by the existing fixed-system-UUID pattern rather than introducing user or multi-credential abstractions.
  Rationale: This installation is single-user and the requested `backup_credentials` table represents the current durable credential, not SCD2 history.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Keep the refresh token in the API-owned `backup_credentials` table, encrypted with AES-256-GCM, and never in `backup_configurations`.
  Rationale: Configuration history and secret history have different lifecycles. Replacing one encrypted row avoids accumulating historical secret copies while preserving SCD2 folder configuration history.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Use the credential UUID as AES-GCM associated data in the exact form `dojo:backup-google-drive:<credential_id>`.
  Rationale: Authentication binds ciphertext to its stable logical credential identity and prevents silent transplantation between credential types.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Treat an OAuth callback refresh token as durable backup authorization immediately, before folder selection.
  Rationale: Aspire migration must reach folder Picker without a second consent screen, and the API must be able to broker access after a restart.
  Date/Author: 2026-09-12 / implementation agent
- Decision: If a callback omits a refresh token, preserve an existing encrypted credential but mark a missing-credential case as requiring Drive reauthorization.
  Rationale: Google may omit a refresh token on reuse; overwriting a healthy durable credential would unnecessarily degrade backups, while a first authorization without one cannot support unattended access.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Use Google Picker only through a small browser adapter, and use direct Google Drive HTTP calls for server verification.
  Rationale: The requested frontend boundary keeps global script orchestration out of Vue, while server-side metadata plus write/delete verification proves the selected folder is usable without rclone in a request handler.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Give backup workers only short-lived access tokens through `/api/internal/backup-access`.
  Rationale: Long-lived refresh credentials, the encryption master key, and OAuth client secrets remain API-owned. A token-expiry failure may fail one run and retry later rather than expanding worker authority.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Extract one platform-neutral upload implementation and call it from both Kubernetes orchestration and local rehearsal.
  Rationale: The storage snapshot/PVC lifecycle is Kubernetes-specific, but staging, restic, token brokering, cleanup, and restore verification must not diverge between production-shaped and local tests.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Keep the worker's rclone token envelope access-token-only and do not supply an expiry timestamp that could trigger a refresh attempt.
  Rationale: The worker has no refresh token or OAuth client secret by design; a token-expiry failure is allowed to fail the run and be retried later.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Keep rehearsal remote cleanup in the shared uploader, with a path guard that rejects `dojo/restic` and all non-rehearsal paths.
  Rationale: The local command must be unable to prune or delete the production repository while still reusing API broker credentials and rclone setup.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Determine application backup health locally from durable-credential presence plus latest run status, without making Google network calls during app status/readiness.
  Rationale: API startup and readiness must remain available during Drive outages; the broker and explicit backup setup flow handle authorization failures without blocking application use.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Keep `infra/opentofu/google-backup/` as the API-key/project-services root and leave standard consumer Web OAuth client creation manual.
  Rationale: The requested provider resource manages API keys, not the consumer Workspace OAuth client; `google_iam_oauth_client` is not a valid substitute.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Run headless browser checks under a temporary `Xvfb` display when the shell has no display.
  Rationale: This supplies only the missing test runtime service and leaves canonical `just` recipes unchanged.
  Date/Author: 2026-09-12 / implementation agent
- Decision: Keep `build_google_auth_url()` generic but select its scope string only at the explicit OAuth-start route from the purpose-specific constants.
  Rationale: The existing URL helper remains reusable and testable, while no environment-level catch-all scope can accidentally grant Sheets access to Drive-only authorization.
  Date/Author: 2026-09-12 / implementation agent

## Outcomes & Retrospective

Phase 0 and Phase 1 outcome (2026-09-12): The baseline is reproducible under the repository Nix environment with a temporary Xvfb display. The API now has a focused AES-256-GCM credential envelope implementation, a fixed system credential table, new backup configuration identity fields, and a repeatable legacy repair that removes the plaintext token column while preserving configuration values. The service no longer writes the plaintext token. `just migration-check`, `just test-unit` (73 tests), `just test-integration` (80 tests), `just architecture-check`, `just typecheck`, and `just lint` passed. Real OAuth, Drive, Picker, worker, infrastructure, and human gates remain outstanding.

Phase 2 outcome (2026-09-12): OAuth start requests now require an explicit `aspire_migration` or `backup` purpose, with exact purpose-specific scopes and the existing offline/consent parameters. Pending state records that purpose. Callback access tokens remain available in the browser-session store, while returned refresh credentials are encrypted and persisted immediately; missing refresh tokens preserve an existing credential or surface backup reauthorization. The web client submits the purpose explicitly. The Phase 2 gates passed with 97 unit tests, 81 integration tests, migration-check, architecture-check, typecheck, and lint.

Phase 3 outcome (2026-09-12): The API now refreshes durable credentials server-side for Picker sessions and folder configuration, verifies selected folders through direct Drive metadata and zero-byte create/delete probes, and stores canonical folder name plus credential identity. The frontend now uses the isolated Google Picker adapter and minimal backup setup states, including cancel-safe selection and reauthorization fallback. Phase 3 passed with 98 unit tests, 81 integration tests, 275 Cypress component tests plus web unit tests, typecheck, lint, and production web build.

Phase 4 outcome (2026-09-12): The existing internal bearer-authenticated router now brokers only short-lived access tokens and the configured folder ID after validating the encrypted API-owned credential. One platform-neutral uploader requests that broker token, creates an ephemeral access-token-only rclone config, initializes/backups/checks/restic, applies retention when requested, returns the snapshot ID, and removes the config. Kubernetes keeps snapshot/clone/Job orchestration and no longer reads or mounts Google credential files. Phase 4 passed with 105 unit tests, 85 integration tests, architecture-check, typecheck, lint, k8s-render, and a clean deployment refresh-token search.

Phase 5 outcome (2026-09-12): `ops/drive/rehearse.sh` now requires a healthy local API and local restic password/status-token files, creates and prepares a temporary DuckDB, uploads through the shared broker/uploader, restores through the same module to a different target, verifies the material with dojo backup verification, and purges only its unique rehearsal repository in an exit trap. Deterministic tests cover upload failure cleanup, restore target separation, production-path refusal, and purge config cleanup. Phase 5 passed with 108 unit tests, 85 integration tests, lint, and typecheck; the live rehearsal remains deliberately manual.

Phase 6 outcome (2026-09-12): Ready workspaces remain usable with degraded backup status when credentials are absent or the latest scheduled run failed, while new PENDING onboarding remains in `backup_setup` and not ready. The existing single App warning remains the repair entry point and its navigation regression is covered. Upgrade/compatibility fixtures and API state tests pass alongside the web suites: 111 unit tests, 88 integration tests, 45 web unit tests, 275 Cypress component tests, migration-check, typecheck, and lint.

Phase 7 outcome (2026-09-12): OpenTofu now enables exactly Drive, Sheets, Picker, and API Keys services, creates a restricted Picker browser key with configurable deployed referrers, and exposes the project number as Picker App ID plus key output. The API deployment receives references to Web OAuth, Picker, status, and encryption-key secrets; the backup worker receives only data, restic, and internal status/broker access. The obsolete Google backup Secret example and restore-file dependency are gone. `just drive-infra-fmt-check`, `just drive-infra-validate`, and `just k8s-render` pass. Current docs still need alignment before the documentation phase.

At each later major milestone, record what behavior became demonstrable, which gates passed, and any remaining gap. At completion, compare the result against the purpose above and explicitly list anything that could not be validated without staging or production. Production deployment must remain unperformed.

## Context and Orientation

The repository root is `/workspace/dojo2`. The backend is FastAPI and Python under `api/src/dojo/`; it persists domain data in DuckDB through `DojoService` and `Database`. Schema creation is explicit in `api/src/dojo/migrations.py`, with fresh schema SQL under `api/src/dojo/sql/schema/current.sql` and repeatable compatibility repairs under `api/src/dojo/sql/schema/migrations/`. SCD2 means a table keeps historical versions with validity timestamps and one current row; `backup_configurations` uses that model. The new `backup_credentials` table deliberately does not.

Google OAuth currently lives in `api/src/dojo/google.py`. `OAuthTokenStore` keeps browser-session OAuth state and access tokens in process memory. `PendingOAuthAuthorization` binds OAuth state to a session and frontend origin. OAuth HTTP routes, onboarding, backup settings, and internal backup status are in `api/src/dojo/api/routes.py` and `api/src/dojo/api/internal_backup.py`. Domain persistence and readiness shaping are in `api/src/dojo/service.py`. Settings are in `api/src/dojo/api/settings.py` and must stop using a single `GOOGLE_OAUTH_SCOPES` setting.

The existing `api/src/dojo/drive_backup.py` exchanges refresh tokens and uses rclone both to build a config and verify a folder. It will become the shared low-level Google token and direct-Drive behavior boundary; request-time verification must no longer invoke rclone. `api/src/dojo/backup.py` already prepares, verifies, and restores staged DuckDB copies with manifests. The new platform-neutral uploader must reuse that machinery without owning Kubernetes API calls.

The Vue frontend is under `web/src/dojo/`. `OnboardingPage.vue` owns the onboarding step state, `state/app.ts` owns bootstrap and OAuth popup behavior, `api/client.ts` owns HTTP calls, `types.ts` owns response contracts, and `App.vue` already renders the single degraded-backup warning and routes repair to `/onboarding?backup=repair`. Existing design-system components such as `Button`, `Surface`, `Inline`, `TextField`, feedback components, and typography tokens must be reused.

Kubernetes snapshot orchestration is in `ops/k8s/snapshot-backup.sh` and checked-in manifests under `deploy/k8s/base/`. It may continue to create a `VolumeSnapshot`, clone it to a temporary PVC, launch a child Job, report status, and clean temporary resources. The child Job must no longer mount or read Google credentials. The local rehearsal is `ops/drive/rehearse.sh` and the command is `just drive-rehearsal`; it must not use kubectl or modify `dojo/restic`.

The OpenTofu root is intentionally retained at `infra/opentofu/google-backup/`. It will manage only the specified Google project services, a restricted `google_apikeys_key`, and the numeric project-number output. The standard Google Auth Platform Web OAuth client remains a documented manual bootstrap item; do not add `google_iam_oauth_client` or deprecated IAP OAuth resources.

The root `justfile` is the command interface. Use `just setup`, `just check`, `just test-unit`, `just test-integration`, `just test-web`, `just typecheck`, `just lint`, `just architecture-check`, `just migration-check`, `just k8s-render`, `just drive-infra-*`, `just drive-rehearsal`, and `just ci` as specified below. When Cypress is required in this headless environment, start a temporary `Xvfb` and run the unchanged recipe with `DISPLAY=:99`; do not replace repository recipes with ad hoc test commands.

## Plan of Work

### Phase 0: baseline and plan

The baseline is now known: the original worktree was clean on `master`, the required documents were read, setup succeeded, and the full `just check` passed under a temporary display after the authorized formatting and minimal type-only repairs. The plan-only commit is complete. The authorized formatting/type repairs remain visible in the Phase 1 working diff and are included with the first independently verified implementation milestone rather than hidden in the plan commit.

Run from `/workspace/dojo2`:

    git status --short
    git branch --show-current
    git add docs/plans/google-drive-user-oauth-backups.md
    git commit -m "docs: plan user OAuth Google Drive backups"

Do not push. After the commit, inspect `git status --short` and confirm only the expected pre-feature baseline repairs remain unstaged.

### Phase 1: encrypted credential persistence

Add `cryptography` to the normal API project dependencies in `api/pyproject.toml` and refresh the lock file through the repository setup mechanism. Create `api/src/dojo/backup_credentials.py` with narrowly scoped functions for loading the base64 key from `DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE`, encrypting, decrypting, and parsing the `v1:<base64(nonce || ciphertext-with-GCM-tag)>` envelope. Require exactly 32 decoded key bytes, use AESGCM with a random 12-byte nonce for each encryption, use key version 1, and bind authenticated data to `dojo:backup-google-drive:<credential_id>`. Invalid paths, base64, lengths, versions, envelopes, keys, or authentication must fail with clear non-secret errors. This module must not perform Google HTTP calls.

Define `backup_credentials` in `api/src/dojo/sql/schema/current.sql` with the six logical fields `credential_id`, `encrypted_refresh_token`, `granted_scopes`, `key_version`, `created_at`, and `updated_at`; use the fixed system credential UUID pattern already used by dojo. Add the required compatibility migration under `api/src/dojo/sql/schema/migrations/` and invoke it repeatably from `api/src/dojo/migrations.py`. It must remove `backup_configurations.google_drive_refresh_token` without reading or copying its value, preserve folder/status/history/unrelated fields, and preserve already-existing backup rows while adding the new table if absent. The fresh schema must not contain the plaintext column. Update `backup_configurations` and its current view to store `credential_id` alongside folder ID/name and verification state.

Move credential persistence into service-level code, replacing `configure_backup_folder()` token storage with a current single-row upsert/replace operation. Keep SCD2 configuration versioning intact. Make fresh pending provisioning work without any credential. Do not expose credential row contents through service or HTTP responses. Add tests in `api/tests/test_migrations.py`, a focused credential test module, and relevant service tests for key loading errors, round trips, nonce uniqueness, associated-data and wrong-key authentication failures, plaintext absence, fresh schema, compatibility repair preservation, and fresh provisioning.

Run from `/workspace/dojo2`:

    just migration-check
    just test-unit
    just test-integration
    just architecture-check
    just typecheck
    just lint

The milestone is accepted only when all pass and the tests prove both fresh and pre-v1 database shapes. Update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`, then commit all Phase 1 files with:

    git add ...
    git commit -m "feat: encrypt persisted Google backup credentials"

Do not push.

### Phase 2: purpose-specific OAuth and refresh-token capture

In `api/src/dojo/api/settings.py`, replace the catch-all scope setting with explicit constants: Aspire migration has exactly Sheets readonly plus `drive.file`; backup has exactly `drive.file`. Keep the OAuth client ID, secret, and redirect settings. Preserve `access_type=offline`, `include_granted_scopes=true`, and `prompt=consent` in `build_google_auth_url()`.

Extend the request model and `POST /api/onboarding/google/start` so the body contains exactly `purpose: "aspire_migration" | "backup"`; do not infer it from page state. Extend `PendingOAuthAuthorization` with purpose. Continue storing the callback access token in the existing browser-session store for migration. When a callback response contains a refresh token, immediately encrypt and persist it in `backup_credentials` with granted scopes and timestamps. Never return it or include it in callback HTML, API status, logs, or frontend state. If no refresh token is returned, retain a valid existing encrypted credential; otherwise expose a machine-detectable backup-reauthorization condition without blocking a legacy ready application.

Keep Sheets import able to use the in-memory access token after callback. Add backend tests in `api/tests/test_google.py`, settings tests, and route/integration tests proving exact scope sets, state purpose, encrypted persistence, no response secret leakage, preserved credential behavior, missing-credential reauthorization, and migration access-token continuity.

Update the frontend client and app state so migration calls OAuth with `purpose: "aspire_migration"`, while backup setup calls it with `purpose: "backup"` only when the backend says durable authorization is absent or reauthorization is required. Do not invoke OAuth again during Aspire completion when authorization is already durable.

Run:

    just test-unit
    just test-integration
    just migration-check
    just architecture-check
    just typecheck
    just lint

After all pass, update this plan and commit:

    git commit -m "feat: split Google OAuth by authorization purpose"

Do not push.

### Phase 3: direct Drive verification and Google Picker

Refactor `api/src/dojo/drive_backup.py` so low-level Google refresh-token exchange is centralized and reusable by Picker sessions, folder verification, and the broker. Use `httpx` for Drive API calls. Implement folder verification as metadata fetch, folder MIME-type check, canonical name extraction, creation of one zero-byte uniquely named `.dojo-access-probe-<uuid>` file in the selected folder, deletion of that file, and return of canonical ID/name only after both operations succeed. Attempt cleanup whenever a probe was created, including partial failures. Translate invalid/revoked authorization and Drive failures into safe machine-detectable errors without including tokens, ciphertext, keys, or client secrets. Do not invoke rclone in a FastAPI request handler.

Add `GET /api/google/drive/picker-session`. It must obtain a fresh access token server-side from the encrypted credential and return only `access_token`, `expires_in`, `picker_api_key`, and `picker_app_id`. Add settings for `GOOGLE_PICKER_API_KEY` and numeric `GOOGLE_PICKER_APP_ID`; never return client secrets, refresh tokens, ciphertext, or credential rows. Update `PUT /api/settings/backup` to accept only `{folder_id}`; use the durable credential, verify the folder directly, then store canonical folder ID/name, credential ID, and `verified_at`. It must not require the backup-status token file merely to configure a folder. Update backup settings responses with durable-authorization, Picker-availability, configured-folder, and reauthorization state booleans, without secrets.

Create `web/src/dojo/googlePicker.ts` as the only module that touches the Google Picker global. Export one narrow async function accepting `accessToken`, `pickerApiKey`, and `pickerAppId`, returning `{ id: string; name: string } | null`. Load the Google Picker API and use `PickerBuilder`, `DocsView`, `setIncludeFolders(true)`, `setSelectFolderEnabled(true)`, folder MIME type filtering where needed, one selection, and cancel-to-null semantics. Keep API calls and OAuth out of this adapter. Add fake-global adapter tests that never open real Picker.

Update `web/src/dojo/api/client.ts`, `types.ts`, `state/app.ts`, and `OnboardingPage.vue`. Preserve the current visual language and use existing Button, Surface, Inline, feedback, and typography components. Replace service-account copy and editable folder-ID TextField with the minimal requested states: `BACKUPS`, “Back up dojo to Google Drive”, the explanatory copy, “Connect Google Drive”, “Choose folder”, canonical “Backup folder” name, and “Continue to app”. Picker cancellation leaves the screen unchanged. Picker selection sends only the ID to the backend; canonical name comes from the verified response. A reauthorization error returns the screen to Connect Google Drive. Ensure migration completion enters backup setup without another OAuth call, while Start empty invokes backup-purpose OAuth.

Add frontend coverage for all listed states and transitions, including repair query reuse. Run from `/workspace/dojo2` with a temporary `Xvfb` display for Cypress:

    DISPLAY=:99 just test-web
    just typecheck
    just lint
    just build-web
    just test-unit
    just test-integration

Update this plan and commit:

    git commit -m "feat: select Google Drive backup folder with Picker"

Do not push.

### Phase 4: broker and platform-neutral uploader

Under the existing internal backup router, add `POST /api/internal/backup-access`, protected by the same bearer token mechanism used by backup status reporting. It returns only `access_token`, `expires_in`, and `folder_id`, and only when a current backup configuration references an existing encrypted credential that decrypts and is accepted by Google. Map missing/invalid configuration, missing credential, bad ciphertext, and revoked refresh tokens to clear machine-detectable failures without secret material. Add tests for missing and incorrect bearer tokens, all failure cases, success shape, and response secret absence.

Extract a repository-consistent platform-neutral Python uploader/module under `api/src/dojo/`. Its only Google credential source is the broker endpoint and its input is a prepared staging directory plus internal API URL/token and the existing restic password/configuration inputs. It must request the short-lived token, build an ephemeral rclone config, initialize a restic repository if absent, back up the prepared staging directory, run `restic check`, apply current retention when appropriate, return the snapshot ID, and remove temporary config files on exit. It must not read DuckDB for credentials and must not contain Kubernetes API calls. Add deterministic tests mocking httpx and subprocess boundaries.

Update `ops/k8s/snapshot-backup.sh` so Kubernetes continues to own snapshot, clone, Job, status, cleanup, and retention orchestration, while the child Job calls the shared uploader. Remove reads of `/google-backup/client-id`, `/google-backup/client-secret`, `/google-backup/refresh-token`, the Google volume, and its mount. The worker receives only prepared data, restic password, internal bearer token, and API network access. It must not receive the encryption key or OAuth client secret. Preserve existing status evidence and phase reporting unless directly required by this boundary.

Run:

    just test-unit
    just test-integration
    just architecture-check
    just typecheck
    just lint
    just k8s-render
    git grep -n "refresh-token" deploy ops

Inspect rendered manifests. Any active backup-worker refresh-token mount or file reference fails the milestone; historical prose is permitted only when explicitly historical. Update the plan and commit:

    git commit -m "feat: broker short-lived credentials to Drive backup workers"

Do not push.

### Phase 5: local Drive rehearsal

Rewrite `ops/drive/rehearse.sh` and its `just drive-rehearsal` behavior to require a running local dojo API with the encrypted credential and configured folder. It must call the same `/api/internal/backup-access` endpoint and shared uploader as Kubernetes. It must provision a temporary test DuckDB, prepare/checkpoint it with existing backup machinery and a manifest, create a unique repository only under `dojo-rehearsals/<unique-id>/restic` inside the configured folder, upload, run restic check, locate the snapshot, restore to a different temporary local target, run normal dojo backup verification, remove only the created remote rehearsal repository, and clean all local temporary data. It must refuse `dojo/restic`, production repository pruning, kubectl, PVCs, VolumeSnapshots, ServiceAccounts, service-account JSON, and mounted credential files. Cleanup must be attempted after success and failure.

Add mocked and temporary-directory tests for unique remote path, production-path refusal, separate restore target, verification, remote cleanup on both outcomes, and no production prune. Do not run live rehearsal yet. Run:

    just test-unit
    just test-integration
    just lint
    just typecheck

Update the plan and commit:

    git commit -m "feat: add local Google Drive backup rehearsal"

Do not push.

### Phase 6: legacy readiness and repair UX

Use the existing warning in `web/src/dojo/App.vue`; do not add another banner or settings page. Ensure a new onboarding flow with explicit `PENDING` backup configuration has `ready=false` and `mode=backup_setup`, while successful configuration has `ready=true`. Ensure a previously ready application with no encrypted credential, an unverified/missing folder, a revoked credential, or a failed latest scheduled backup remains ready with `backup.state=degraded`. Repair continues to navigate to `/onboarding?backup=repair` and reuses the same setup UI. A missing credential after compatibility repair must not block startup or onboarding for a legacy ready application.

Add backend integration tests for all four states and at least one upgrade fixture from a database created before encrypted credentials existed. Add web tests for normal opening, persistent warning, repair navigation, Connect Google Drive visibility, successful repair, and warning removal after healthy configuration. Run:

    just test-integration
    DISPLAY=:99 just test-web
    just migration-check
    just typecheck
    just lint

Update the plan and commit:

    git commit -m "fix: keep legacy workspaces usable while backups are degraded"

Do not push.

### Phase 7: OpenTofu and service-account removal

Keep `infra/opentofu/google-backup/` in place. Replace service-account resources, variables, outputs, and active documentation with exactly project services `drive.googleapis.com`, `sheets.googleapis.com`, `picker.googleapis.com`, and `apikeys.googleapis.com`. Add a restricted `google_apikeys_key` whose application restrictions include `http://localhost:5173/*`, `https://docs.google.com/*`, and a variable-driven list of deployment-specific additional allowed referrers. Its API restrictions permit exactly `picker.googleapis.com` and `drive.googleapis.com`. Obtain the Google Cloud project number from the project data source, expose it as Picker App ID output, and expose `picker_api_key` and `picker_app_id`, marking the key output sensitive if provider tooling requires it. Do not create `google_iam_oauth_client` or deprecated IAP resources. The ordinary Google Web OAuth client remains a manual bootstrap item.

Remove active Kubernetes/examples for `dojo-backup-google` when unused, but retain the ordinary dojo Web OAuth Secret needed by FastAPI. Update deployment configuration so only the API receives OAuth client settings and `DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE`; the backup Job does not receive either. Preserve public `just drive-infra-*` recipe names. Update `.env.example` with safe names/placeholders for the required local variables, ensure `.env` and `.local` are ignored, and never create or print credential values.

Run:

    just drive-infra-fmt
    just drive-infra-fmt-check
    just drive-infra-validate
    just k8s-render
    git grep -n "backup_service_account" .
    git grep -n "dojo-backup-google" .
    git grep -n "google_drive_refresh_token" .

Interpret historical changelog/decision references separately from active code/config. Any active obsolete dependency fails. Update the plan and commit:

    git commit -m "infra: replace Drive backup service account with Picker configuration"

Do not push.

## Human Gate A: Google infrastructure plan

Stop coding after Phase 7. Run from `/workspace/dojo2`:

    just drive-infra-plan

Show only a concise summary of APIs to enable, service-account resources to destroy, the Picker API key to create, allowed referrers, and the Picker App ID/project-number output. Never paste an API-key value or any state/output secret. Ask the user to explicitly approve applying the plan. Do not run `just drive-infra-apply` until approval. After approval, run it, record only non-secret success/failure evidence in this plan, and do not commit generated state, tfvars, credentials, or secret outputs.

## Human Gate B: manual Google OAuth client configuration

Stop and provide exactly these local values, without requesting client IDs or secrets:

    Authorized JavaScript origin:
    http://localhost:5173

    Authorized redirect URI:
    http://localhost:8000/api/onboarding/google/callback

Tell the user not to remove existing production origin or redirect entries. Ask the user to verify that the OAuth application is not relying on Google's temporary Testing-mode refresh-token behavior for long-lived unattended backups. Wait for explicit confirmation that configuration is complete.

## Phase 8: local environment preparation

Document the local runtime variables using the existing API `.env` mechanism, with safe placeholders only in `.env.example`:

    GOOGLE_OAUTH_CLIENT_ID
    GOOGLE_OAUTH_CLIENT_SECRET
    GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/onboarding/google/callback
    GOOGLE_PICKER_API_KEY
    GOOGLE_PICKER_APP_ID
    DOJO_CREDENTIAL_ENCRYPTION_KEY_FILE
    BACKUP_STATUS_TOKEN_FILE

Do not generate credential values in the repository or display them. The user may generate 32 random bytes, base64-encode them, and store them at an ignored local path. The backup status token likewise belongs only in an ignored local file. Confirm `.env`, `.local/`, and local secret paths are ignored before proceeding.

## Human Gate C: real local Start-empty flow

Before asking the user to click, start a temporary `Xvfb` if needed and verify both `GET http://localhost:8000/health` and `GET http://localhost:8000/api/health` are healthy. Ask the user to use an isolated database, start the API from the repository root with:

    DUCKDB_PATH=.local/drive-backup-start-empty.duckdb just api

Start the web app in a second terminal with:

    just web

Ask the user to open `http://localhost:5173` and select Start empty. Observe logs without logging credentials. The user must confirm backup setup appears; no service-account email or editable folder-ID input appears; Connect Google Drive requests Drive access but not Sheets access; consent returns to backup setup; Choose folder opens real Picker; a dedicated temporary Drive folder can be selected; the canonical folder name appears; Continue to app loads dojo. If any step fails, return to implementation and repeat this gate. Record pass/fail evidence and non-secret symptoms here before migration testing.

## Human Gate D: real local Aspire migration flow

Stop the API and restart it with a different isolated database:

    DUCKDB_PATH=.local/drive-backup-aspire.duckdb just api

Keep the frontend running, reload `http://localhost:5173`, and ask the user to select Migrate from Aspire, enter a valid Aspire Sheet ID, and submit. Confirm exactly one OAuth consent interaction requests both Sheets readonly and Drive file access. Complete analysis, review, and commit. Continue from migration completion to backup setup; no second consent appears; Picker opens directly; canonical name appears; Continue loads imported data.

Afterward inspect database structure without selecting or printing secret contents. Confirm `backup_credentials` exists, `backup_configurations` has no plaintext refresh-token column, current configuration references a credential, and an encrypted credential row exists. Record only structural results and non-secret errors in this plan. A second consent after migration is a failure requiring implementation correction and repeat.

## Human Gate E: existing-user upgrade and repair

Use an automated fixture or temporary database representing a ready application with data and no encrypted credential. Never use the user's ordinary database. Start the app against it and ask the user to verify the app opens normally, the global Backups need attention warning appears, Repair backups opens `/onboarding?backup=repair`, Connect Google Drive appears, authorization and Picker repair the state, and returning to the application removes the warning after healthy configuration. Record the non-secret result here. This gate must pass before the live rehearsal.

## Human Gate F: real local Drive backup and restore rehearsal

Explain that `just drive-rehearsal` will write a temporary restic repository below the currently selected Drive folder and delete that repository afterward. Obtain explicit user approval before running it. Use the same local API that contains the encrypted credential and folder configuration. Run:

    just drive-rehearsal

Observe only non-secret evidence: temporary DuckDB creation, preparation and manifest, successful broker call, unique `dojo-rehearsals/...` repository, restic backup/check, snapshot ID, local restore to a different target, normal dojo verification, remote cleanup, and local temporary cleanup. Confirm it never touches `dojo/restic` and never prunes production. If it fails, fix locally and repeat until green. The user may optionally verify that no rehearsal folder remains in Drive. Record the result here.

## Phase 9: documentation alignment

Only after behavior and the human local gates work, update current documentation in `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHANGELOG.md`, `docs/src/deployment-provisioning.md`, `docs/src/backup-and-restore.md`, and only materially changed contributor procedure in `CONTRIBUTING.md`. Do not change `DESIGN.md` unless a reusable visual-system rule genuinely changes.

`SPEC.md` must state that backup setup is required for new workspaces; Aspire uses one combined OAuth grant; Start empty uses Drive-only authorization; Picker chooses folders; existing users remain usable and see Repair backups; remote backup failure does not block application use. `ARCHITECTURE.md` must describe encrypted credentials, master-key boundary, browser access token versus persisted refresh token, Picker session, direct Drive verification, broker, shared uploader, Kubernetes snapshot boundary, and local rehearsal. Append durable decisions to `DECISIONS.md` for user OAuth, `drive.file` plus Picker, AES-256-GCM, API-owned refresh tokens and worker short-lived tokens, manual standard Web OAuth bootstrap, and required local rehearsal.

Remove current active instructions about sharing with a service-account email, onboarding writing a refresh token into a Kubernetes Secret, or rclone using a service-account file. Clearly historical changelog/decision prose may remain marked historical. Update this plan with documentation evidence, then commit:

    git commit -m "docs: document user OAuth Google Drive backup architecture"

Do not push.

## Phase 10: complete local automated gate

Use a temporary `Xvfb` display when needed, but run the canonical commands unchanged:

    just check
    just ci
    just drive-infra-fmt-check
    just drive-infra-validate
    just k8s-render

Review:

    git status --short
    git log --oneline --decorate -n 15
    git diff master...HEAD --stat
    git grep -n "google_drive_refresh_token" .
    git grep -n "backup_service_account" .
    git grep -n "dojo-backup-google" .
    git grep -n "refresh-token" deploy ops api web

Inspect the complete diff for credential values, unrelated edits, active service-account code, plaintext persistence, duplicate upload implementations, and Kubernetes assumptions in shared backup code. Historical references must be explicitly historical. Update all living-plan sections with final evidence. If the plan changed after the documentation commit, commit only the plan outcome with:

    git commit -am "docs: record Google Drive backup implementation outcome"

Do not push.

## Human Gate G: local completion approval

Stop and report only concise, non-secret evidence: local commit list; `just check`; `just ci`; Start-empty result; Aspire migration result; existing-user repair result; Drive rehearsal result; OpenTofu validation result; and known limitations. Explicitly ask:

    Local implementation and validation are complete. Do you want me to push the feature branch and open the PR?

Do not push unless the user says yes.

## Phase 11: GitHub and CI after explicit approval

Push only `feat/google-drive-user-oauth-backups`, never directly to `master`, and open a PR against `master` with a credential-free description covering service-account removal, purpose-specific scopes, encrypted refresh-token persistence, Picker, broker, shared local rehearsal, OpenTofu, and local test evidence. Do not include account information or screenshots. Wait for CI. If CI fails, inspect the exact failure, reproduce it locally where possible, fix it, run the narrow gate, `just check`, and `just ci`, commit the fix, push, and wait again. Never merge red CI.

## Human Gate H: staging promotion approval

After PR CI is green, stop and report the green result. Ask for explicit approval to merge/promote to staging. Do not merge or deploy before approval.

## Phase 12: merge, image publication, and staging

After approval, use the repository's existing merge policy. Let the `master` workflow publish the staging image and record its immutable digest. Do not deploy a mutable local image. If the external staging deployment workspace is unavailable, stop after reporting that master CI is green, the image is published with its digest, and the deployment configuration is absent; ask the user to point to the existing workspace. Do not invent a deployment model and do not deploy production.

When the existing staging mechanism is available, update only the staging image reference needed for this version and use its canonical workflow. Verify health endpoints, migration without Drive on the critical path, normal app startup, legacy readiness/degraded repair behavior, onboarding setup, staging redirect URI, Picker from staging origin, direct folder verification, broker access from CronJob without mounted refresh credentials, one successful manual backup, successful status, and absence of refresh tokens or encryption keys from worker environment, volumes, logs, and pod descriptions. Ask the user to perform browser OAuth and Picker clicks where required.

## Concrete Steps

All commands below run from `/workspace/dojo2` unless a command explicitly changes directory through an existing `just` recipe. Never replace a suitable `just` recipe with direct pytest, pnpm, uv, ruff, mypy, or tofu commands. For browser checks in this environment, use a temporary display wrapper around the canonical recipe:

    Xvfb :99 -screen 0 1280x1024x24 >/tmp/dojo-xvfb.log 2>&1 &
    DISPLAY=:99 just check

The display process must be stopped after the command. Do not store its log in the repository. Every milestone has its own verification commands above. Keep generated `dist/`, `.local/`, `.venv/`, Cypress state, OpenTofu state, tfvars, credentials, and output secrets ignored and out of commits.

## Validation and Acceptance

Automated acceptance is milestone-specific and cumulative. Credential encryption tests must prove that no plaintext refresh token is in a database row and no HTTP response includes encrypted credential contents. OAuth tests must prove exact purpose-specific scope sets and one combined Aspire consent path. Drive tests must prove direct metadata and write/delete verification with cleanup. Picker tests must stub the global API and prove cancellation, one selection, folder inclusion, and returned ID/name. Broker tests must prove bearer authentication, decryption/revocation failures, response shape, and absence of secret material. Uploader/rehearsal tests must mock network and subprocess boundaries and prove production repository refusal and cleanup on both success and failure. Readiness tests must prove new-user blocking versus legacy degraded readiness.

Real local acceptance is behavioral: Start empty has one Drive-only consent and Picker selection; Aspire has one combined consent and no second consent before Picker; an old ready app opens and repairs through the existing warning; and the rehearsal uploads, checks, restores, verifies, and removes only its temporary remote repository. Infrastructure acceptance is a reviewed OpenTofu plan/application, rendered manifests without backup credential mounts, and no active service-account dependencies. Final acceptance additionally requires `just check`, `just ci`, infrastructure validation, and a clean diff review before the push approval gate.

## Idempotence and Recovery

Schema provisioning and compatibility repairs must be repeatable on fresh databases, current databases, and restored pre-v1 databases. The plaintext compatibility repair intentionally invalidates any old plaintext token and must never read or copy it. A missing encrypted credential is a recoverable backup-degraded state, not an onboarding-blocking state for an already-ready app. Credential replacement updates one fixed credential row rather than adding historical secret copies.

Folder verification must delete a created probe on every possible path. The uploader must remove temporary rclone configuration using process-exit cleanup and must never choose the production repository for rehearsal. Rehearsal cleanup must be attempted after upload, restore, verification, and failure; retrying a failed rehearsal must create a new unique subtree and must not prune production. OpenTofu changes must be applied only after Human Gate A approval, with state and credentials excluded from commits. Human browser gates use isolated databases and temporary Drive folders so a failed test can be discarded safely.

If a milestone gate fails, leave the failed tests/log symptom documented in `Surprises & Discoveries`, fix only the relevant implementation, rerun the narrow gate, then the required cumulative gates, and make a small corrective commit when independently verified. Never stash, reset, discard, overwrite, or amend user work. Never print tokens, keys, secrets, ciphertext, or client credentials while diagnosing failures.

## Artifacts and Notes

The expected local history is approximately:

    docs: plan user OAuth Google Drive backups
    feat: encrypt persisted Google backup credentials
    feat: split Google OAuth by authorization purpose
    feat: select Google Drive backup folder with Picker
    feat: broker short-lived credentials to Drive backup workers
    feat: add local Google Drive backup rehearsal
    fix: keep legacy workspaces usable while backups are degraded
    infra: replace Drive backup service account with Picker configuration
    docs: document user OAuth Google Drive backup architecture
    docs: record Google Drive backup implementation outcome

The actual first feature commit may also include the explicitly authorized pre-feature formatting/type correction if it cannot be isolated cleanly without violating the required plan-only commit. Explain that in this plan and in the commit review. Do not add credentials, real folder IDs, account information, API-key values, refresh tokens, encryption keys, or access tokens to this file.

## Interfaces and Dependencies

The API dependency `cryptography` supplies `cryptography.hazmat.primitives.ciphers.aead.AESGCM`. The new credential module owns key-file loading, envelope encoding/decoding, encryption, and decryption. Google HTTP behavior remains in the backend Google/Drive boundary using `httpx`. FastAPI route modules own request/response wiring only; `DojoService` owns persistence and readiness; SQL remains in native files under `api/src/dojo/sql/`.

The OAuth start request is `POST /api/onboarding/google/start` with exactly one purpose field. The picker session is `GET /api/google/drive/picker-session` and returns exactly `access_token`, `expires_in`, `picker_api_key`, and `picker_app_id`. Folder configuration is `PUT /api/settings/backup` with only the selected folder ID in the request body and canonical verified folder information in the response. The internal broker is `POST /api/internal/backup-access`, authenticated by the existing backup bearer token, and returns exactly `access_token`, `expires_in`, and `folder_id`.

`backup_credentials` stores one fixed system UUID, encrypted refresh token, granted scopes, key version 1, and created/updated timestamps. `backup_configurations` remains SCD2 and stores folder ID, canonical folder name, credential ID, verification state, and existing unrelated configuration data. The frontend adapter `web/src/dojo/googlePicker.ts` accepts `accessToken`, `pickerApiKey`, and `pickerAppId` and resolves a selected `{ id, name }` or `null` on cancel. The shared uploader accepts a prepared staging directory and broker URL/token inputs; its implementation must be callable by both the Kubernetes child Job and `ops/drive/rehearse.sh`.

## Revision Note

2026-09-12: Created this living plan after baseline setup and research. Recorded the clean initial worktree, local feature branch, temporary Xvfb requirement, authorized baseline repairs, current architecture mismatch, exact phase sequence, human gates, security boundaries, and recovery rules. Future revisions must update all living sections and append a new revision note explaining what changed and why.

2026-09-12: Marked Phase 0 complete and Phase 1 verified. Recorded the pinned-`uv` lockfile correction, encrypted credential module, fresh schema, plaintext-column repair, service persistence removal, and Phase 1 gate results. The next revision must document Phase 1's commit and begin purpose-specific OAuth.

2026-09-12: Marked Phase 2 verified. Recorded exact purpose-specific scope selection, pending purpose state, immediate encrypted callback persistence, missing-refresh-token behavior, the canonical unit-suite inclusion of `test_google.py`, and the 97-unit/81-integration gate results. The next revision must document Phase 2's commit and begin direct Drive verification and Picker.

2026-09-12: Marked Phase 3 verified. Recorded direct Drive metadata/probe verification with cleanup, the browser-safe Picker session contract, canonical folder persistence, isolated Picker adapter, minimal backup setup UI, and backend/frontend gate results. The next revision must document Phase 3's commit and begin the internal broker and shared uploader.

2026-09-12: Marked Phase 4 verified. Recorded the internal bearer-protected token broker, access-token-only ephemeral uploader config, shared restic execution, Kubernetes worker boundary, deleted obsolete backup Secret example, and 105-unit/85-integration gate results. The next revision must document Phase 4's commit and begin the local Drive rehearsal.

2026-09-12: Marked Phase 5 verified. Recorded the local API health prerequisite, unique rehearsal path, shared upload/restore/purge implementation, production repository guard, temporary local data cleanup, and 108-unit/85-integration gate results. The next revision must document Phase 5's commit and begin legacy readiness and repair behavior.

2026-09-12: Marked Phase 6 verified. Recorded degraded readiness semantics, latest-run/credential health gating, existing warning repair routing, upgrade fixture coverage, and 111-unit/88-integration/web gate results. The next revision must document Phase 6's commit and begin OpenTofu and active service-account removal.

2026-09-12: Marked Phase 7 verified. Recorded the retained OpenTofu root, exact API services, restricted Picker key, project-number output, API-only long-lived secret boundary, broker-based restore/backup manifests, and infrastructure gate results. The next stopping point is Human Gate A: run and report `just drive-infra-plan`, then wait for explicit apply approval.
