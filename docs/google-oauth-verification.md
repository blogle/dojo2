# Google OAuth Verification Guide for Dojo

> **This document is reusable procedural guidance. It does not contain OAuth client
> secrets, access tokens, refresh tokens, account credentials, or unlisted video
> URLs. Those values belong in Lific comments on DOJO-24, never in source control.**

## 1. Sources and Capture Date

This guide was assembled from the following Google official documentation. The
capture date is **2026-09-14**. Revalidate every requirement against the live
pages immediately before recording verification evidence; do not rely on a stale
copy.

| Source | URL (informational) | Key content |
|---|---|---|
| Sensitive scope verification | developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification | Preparation steps, video requirements, scope justification, submission flow |
| Brand verification | developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification | Consent-screen branding, authorized domains, home-page and privacy-policy requirements |
| OAuth 2.0 Policies | developers.google.com/identity/protocols/oauth2/policies | Narrowest-scope rule, scope-update obligations, secure origins |
| OAuth app state overview | developers.google.com/identity/protocols/oauth2/production-readiness/overview | Testing vs. published, verified vs. unverified, 100-user cap |
| OAuth 2.0 Scopes reference | developers.google.com/identity/protocols/oauth2/scopes | Scope URIs, sensitivity classification |
| Configure OAuth consent screen | developers.google.com/workspace/guides/configure-oauth-consent | Cloud Console scope configuration UI |

**STOP condition:** If Google's live documentation has changed since the capture
date and the change affects scope classification, video requirements, or the
submission flow, update this section and the relevant checklist before proceeding
with capture.

## 2. Exact Submitted OAuth Scopes

The following scopes are declared in the codebase and are the exact set submitted
for Google OAuth verification. They are defined in `api/src/dojo/google.py` and
`api/src/dojo/constants.py`.

### 2.1 Scope inventory

| Scope URI | Sensitivity | Source constant | Declared in |
|---|---|---|---|
| `https://www.googleapis.com/auth/spreadsheets.readonly` | Sensitive | `GOOGLE_SHEETS_READONLY_SCOPE` (constants.py:50), member of `GOOGLE_ASPIRE_MIGRATION_SCOPES` (google.py:20-23) | `api/src/dojo/google.py` |
| `https://www.googleapis.com/auth/drive.file` | Sensitive | `GOOGLE_DRIVE_FILE_SCOPE` (google.py:19), member of both `GOOGLE_ASPIRE_MIGRATION_SCOPES` and `GOOGLE_BACKUP_SCOPES` (google.py:24) | `api/src/dojo/google.py` |

### 2.2 Purpose-specific scope sets

Dojo requests scopes in two purpose-specific bundles. The `purpose` field is
submitted by the frontend and validated by the backend
(`api/src/dojo/api/models.py:45`, `api/src/dojo/google.py:70-75`).

| Purpose | Scopes requested | When triggered |
|---|---|---|
| `aspire_migration` | `spreadsheets.readonly` + `drive.file` | User selects "Migrate from Aspire" and submits a Google Sheet ID |
| `backup` | `drive.file` only | User selects "Start empty" or completes Aspire migration and enters backup setup |

Both purposes use `access_type=offline`, `include_granted_scopes=true`, and
`prompt=consent` (google.py:58-65).

### 2.3 Stop condition: submitted scope without demonstrable feature

> If a scope appears in the submitted configuration for which there is no
> currently demonstrable user-facing Dojo feature, **stop before recording** and
> report the discrepancy in a Lific comment on DOJO-24 rather than inventing a
> demonstration.

As of the capture date, both submitted scopes have clear user-facing features
described in Section 3. No stop condition is triggered.

## 3. Scope-to-Feature Mapping

Each submitted scope must appear in the verification video with a visible
demonstration of the Dojo feature it enables.

### 3.1 `spreadsheets.readonly` -- Aspire Sheet Import

**User-visible feature:** Reading and importing the user's Aspire Budgeting
Google Sheet during onboarding.

**What the user sees:**

1. On the onboarding screen, the user selects **Migrate from Aspire**.
2. The user enters a Google Sheet ID and clicks **Submit**.
3. The Google OAuth consent screen requests read access to the specified sheet.
4. After granting permission, dojo reads the sheet's named ranges
   (Configuration, Transactions, Category Allocation, Net Worth Reports --
   `constants.py:52-57`), parses the data, and presents a net-worth duplicate
   review screen.
5. The user confirms import decisions and dojo commits the migrated data.

**Evidence checkpoint:** The imported data is visible in the Budget, Transactions,
or Assets & Liabilities pages after migration completes.

**Narrowest-scope justification:** Dojo only reads sheet data; it never writes to
or modifies the user's Google Sheet. `spreadsheets.readonly` is the narrowest
available scope for this API.

### 3.2 `drive.file` -- Encrypted Drive Backup

**User-visible feature:** Encrypted off-site backup of the dojo database to a
user-selected Google Drive folder.

**What the user sees:**

1. During onboarding (after choosing Start empty or completing Aspire migration),
   the backup setup screen shows "Back up dojo to Google Drive" with a
   **Connect Google Drive** button.
2. After authorization (or immediately if authorization was already granted
   during Aspire migration), the user clicks **Choose folder**, which opens
   Google Picker to select a Drive folder.
3. Dojo verifies the selected folder with a direct Drive metadata and zero-byte
   write/delete probe, then displays the canonical folder name as "Backup
   folder."
4. The user clicks **Continue to app** and enters the application.
5. Scheduled backups encrypt the database and upload it to the selected folder.
   If a backup fails, a persistent warning appears with a **Repair backups**
   link.

**Evidence checkpoint:** The canonical backup folder name is visible on the
backup setup screen. After a successful backup run, the encrypted backup artifact
exists in the selected Drive folder.

**Narrowest-scope justification:** `drive.file` grants access only to files
created or opened by the app, not the user's entire Drive. This is the narrowest
scope that supports folder selection via Picker and encrypted upload.

### 3.3 Scope-feature cross-check matrix

| Submitted scope | Demonstrable feature | Evidence checkpoint in video |
|---|---|---|
| `spreadsheets.readonly` | Aspire Sheet import during onboarding | Imported data visible in app after migration |
| `drive.file` | Encrypted Drive backup with user-selected folder | Canonical folder name shown on backup setup screen |

## 4. Test Account and Synthetic Sheet Preparation

### 4.1 Dedicated test Google account

- Create or designate a Google account used exclusively for verification evidence.
- Do not use a personal Google account with real financial data.
- The account language must be set to **English** so the consent screen and any
  Google-supplied warnings render in English.
- The account must not be a Google Workspace organizational account unless the
  OAuth consent screen is configured for Internal user type.

### 4.2 Synthetic Aspire Sheet

- Create a Google Sheet in the test account that follows Aspire Budgeting
  conventions with the named ranges dojo expects:
  `Configuration`, `Transactions`, `Category Allocation`, `Net Worth Reports`.
- Populate with synthetic financial data only -- no real account numbers,
  balances, payees, or personally identifiable information.
- The sheet must be accessible to the test account granting OAuth consent.
- Name the sheet descriptively (e.g., "Dojo Verification Test Sheet") so its
  purpose is clear if a Google reviewer opens it.

### 4.3 Dedicated Drive backup folder

- Create an empty folder in the test account's Google Drive for the backup
  demonstration (e.g., "Dojo Verification Backups").
- This folder will receive encrypted backup artifacts during the recording.

## 5. Revoke Prior Grant Procedure

Before beginning the verification recording, revoke any existing Dojo OAuth grant
from the test account so the real consent flow is displayed:

1. While signed in to the test Google account, navigate to
   `myaccount.google.com/permissions`.
2. Find the Dojo application in the list of connected apps.
3. Click on it and select **Remove access** (or equivalent).
4. Confirm the removal.
5. Verify the app no longer appears in the connected apps list.

After revocation, the next Dojo onboarding attempt will present the full
Google-hosted consent screen rather than silently reusing an existing grant.

## 6. Verification Video Capture Script

> **Critical:** This is a real-browser recording, not a Cypress test or automated
> script. Cypress Aspire artifacts (covered by DOJO-23) never simulate Google
> consent and must not be submitted as verification evidence.

### 6.1 Recording environment

- Use a normal desktop browser (Chrome, Firefox, or equivalent) with standard
  browser chrome visible -- address bar, tab bar, bookmarks bar if present.
- Do not use a headless browser, iframe, overlay, or any technique that hides
  or replaces the real Google-hosted consent page.
- Set the browser window to a reasonable size (e.g., 1280x800 or larger) so
  text on the consent screen is legible.
- Ensure the browser and OS language are English.
- The dojo application must be the same OAuth client/application being submitted
  for verification.

### 6.2 Recording script -- Aspire migration path

Record the following sequence in one continuous take. Pause long enough at each
checkpoint for text to be readable in the recording.

| # | Action | What must be visible | Verification requirement demonstrated |
|---|---|---|---|
| 1 | Open dojo in the browser | Browser address bar showing the dojo URL | App identity |
| 2 | Onboarding screen appears | Product title, "Start empty" and "Migrate from Aspire" choices | App identity |
| 3 | Select **Migrate from Aspire** | Aspire migration form with Sheet ID field | -- |
| 4 | Enter the synthetic Sheet ID and click **Submit** | Form with entered ID | -- |
| 5 | Google OAuth consent screen loads | **Full consent screen with browser chrome visible.** Linger for readability. Must show: (a) app name, (b) OAuth client ID in the address bar, (c) requested scopes with descriptions, (d) user account selector | OAuth consent, app name, client ID, scope declarations |
| 6 | Click **Allow** (or equivalent grant button) | Grant action visible | User consent flow |
| 7 | Migration progress screen | Progress indicator | -- |
| 8 | Net-worth duplicate review screen | Budget accounts, net-worth categories, suggested matches | -- |
| 9 | Confirm review decisions and migration completes | Success message | -- |
| 10 | Navigate to Budget or Transactions page | Imported Aspire data visible in the application | `spreadsheets.readonly` feature demonstration |
| 11 | Continue to backup setup | Backup setup screen with "Back up dojo to Google Drive" | -- |
| 12 | Click **Connect Google Drive** (if not already authorized) | OAuth consent requesting `drive.file` -- browser chrome visible | `drive.file` scope declaration |
| 13 | Click **Choose folder** | Google Picker opens | -- |
| 14 | Select the dedicated backup folder | Picker selection | -- |
| 15 | Canonical folder name appears as "Backup folder" | Folder name displayed on backup setup screen | `drive.file` feature demonstration |
| 16 | Click **Continue to app** | Application shell with imported data loaded | End-to-end flow complete |

### 6.3 Recording script -- Start empty path (supplementary)

If Google requires demonstrating the Start empty path separately:

| # | Action | What must be visible | Verification requirement demonstrated |
|---|---|---|---|
| 1 | Open dojo, onboarding screen | Browser address bar, app identity | -- |
| 2 | Select **Start empty** | Backup setup screen (Drive-only OAuth) | -- |
| 3 | Click **Connect Google Drive** | OAuth consent showing only `drive.file` scope -- browser chrome visible | `drive.file` scope, narrowest-scope compliance |
| 4 | Choose folder with Picker | Picker, canonical name | `drive.file` feature demonstration |
| 5 | Continue to app | Empty application shell | -- |

### 6.4 Capture requirements checklist

During the Google consent portions of the recording:

- [ ] Browser chrome (address bar, tab bar) is fully visible and unobscured
- [ ] The app name is legible on the consent screen
- [ ] The OAuth client ID is visible in the browser address bar
- [ ] The requested permissions/scopes are readable on the consent screen
- [ ] The recording lingers on the consent screen long enough for a reviewer to
      read all elements (at least 5 seconds of still frame)
- [ ] The consent screen is not cropped, overlaid, or replaced by any automation
- [ ] No credentials, tokens, secrets, or real financial data are visible

## 7. Disclosure, Upload, and Submission Checklists

### 7.1 Pre-submission checklist

- [ ] DOJO-8 (granted Sheets scope gate) is complete and the submitted build
      correctly distinguishes Aspire Sheets authorization from Drive backup
      authorization
- [ ] Current Google verification instructions have been revalidated against live
      documentation (update Section 1 if changed)
- [ ] The exact submitted scope set matches what is declared in
      `api/src/dojo/google.py` and the Cloud Console consent screen configuration
- [ ] Every submitted scope has a corresponding visible Dojo feature
      (Section 3.3 matrix is fully checked)
- [ ] The test account's prior Dojo grant has been revoked (Section 5)
- [ ] The synthetic Aspire Sheet contains only synthetic data
- [ ] The recording shows the real Google-hosted consent flow, not a simulation
- [ ] Browser chrome is visible throughout all consent portions
- [ ] No credentials, tokens, or real financial data appear in the recording

### 7.2 Privacy policy disclosure requirements

Google requires the privacy policy to disclose how the application accesses,
uses, stores, and shares Google user data. The privacy policy must:

- [ ] Be publicly accessible (not behind a login)
- [ ] Be hosted on the same domain as the application home page
- [ ] Be linked on the OAuth consent screen in the Cloud Console
- [ ] Disclose that dojo reads Google Sheets data for Aspire migration
- [ ] Disclose that dojo writes encrypted backup files to user-selected Drive
      folders
- [ ] Disclose that refresh tokens are stored encrypted (AES-256-GCM) and that
      workers receive only short-lived access tokens
- [ ] State that Google user data is not shared with third parties

### 7.3 Video upload checklist

- [ ] Upload the recording to YouTube Studio
- [ ] Set visibility to **Unlisted** (required by Google for verification videos)
- [ ] Copy the YouTube URL
- [ ] Record the URL in a **Lific comment on DOJO-24** (not in source control)
- [ ] Confirm the video is playable at the unlisted URL from an incognito window

### 7.4 Cloud Console submission checklist

- [ ] Brand verification is published (not just "Ready to publish")
- [ ] All scopes are declared on the Data Access page in the Cloud Console
- [ ] Sensitive scope justifications are written for each scope (see templates
      below)
- [ ] The unlisted video URL is entered in the YouTube link field
- [ ] Up to three documentation links are provided (home page, privacy policy,
      relevant feature documentation)
- [ ] Developer contact information and support email are current

### 7.5 Scope justification templates

**`spreadsheets.readonly`:**
> Dojo uses this scope to read the user's specified Aspire Budgeting Google Sheet
> during onboarding migration. The app reads named ranges (Configuration,
> Transactions, Category Allocation, Net Worth Reports) to import budgeting data
> into the local application. Dojo never writes to or modifies the user's Google
> Sheet. This is the narrowest available scope for read-only Sheets API access.

**`drive.file`:**
> Dojo uses this scope to create encrypted backup files in a user-selected Google
> Drive folder. The app writes only files it creates (database backups); it does
> not access, read, or modify other files in the user's Drive. The scope is also
> used to verify the selected folder by writing and deleting a zero-byte probe
> file. This is the narrowest available scope that supports app-created file
> access in user-chosen folders.

## 8. Review Artifacts for DOJO-24

After recording, prepare the following artifacts and attach them to DOJO-24 using
deterministic names containing the git short SHA:

| Artifact | Filename pattern | Content |
|---|---|---|
| Storyboard PNG | `google-oauth-verification-<sha>-review.png` | Numbered contact sheet showing key visual checkpoints in order: onboarding, consent screen (with app name, client ID, scopes), grant action, imported data, backup setup, folder selection |
| Manifest TXT | `google-oauth-verification-<sha>-manifest.txt` | Git SHA, build identity, exact submitted scopes, ordered checkpoints, recording date, original video local path and SHA-256, final submitted video URL, review-video checksum |
| Zipped MP4 | `google-oauth-verification-<sha>-video.zip` | Compressed MP4 review copy fitting Lific's 10 MiB decoded attachment limit. Retain original-quality submission video separately |

Add a final Lific comment on DOJO-24 summarizing:

- The scope-to-feature mapping
- The names of the attached review artifacts
- The submitted video URL/location

## 9. Cypress Aspire Artifact Disclaimer

> **Cypress Aspire artifacts (covered by DOJO-23) never simulate Google consent
> and must not be submitted as OAuth verification evidence.** The deterministic
> Aspire migration Cypress recording controls the external Google boundary
> through the Aspire test infrastructure. It does not interact with real
> Google OAuth, the real consent screen, or real Google APIs. Google's
> verification requires evidence of the real Google-hosted authorization
> experience as users will encounter it, which is exclusively a human-browser
> recording task (this document, DOJO-24).

## 10. Limitations and Open Items

1. **Scope classification may change.** Google periodically reclassifies scopes
   (e.g., `drive.file` becoming restricted). Recheck classification in the Cloud
   Console before submission.
2. **Video requirements may evolve.** Google may change the required video
   format, visibility setting, or hosting platform. Revalidate against the live
   sensitive-scope verification page.
3. **Test account setup is manual.** This guide describes what to prepare but
   cannot automate Google account creation, sheet creation, or permission
   management.
4. **No automated consent capture.** The verification video must be recorded by
   a human in a real browser. There is no supported automation path for the
   Google consent portion.
5. **Privacy policy must be live.** The privacy policy URL on the consent screen
   must resolve to a real, current policy before submission.
6. **Brand verification is a prerequisite.** Sensitive scope verification cannot
   begin until brand verification is published. Account for 2-3 business days
   for brand review plus 3-5 business days for sensitive scope review.
7. **Google Workspace admin overrides.** Even after verification, Google Workspace
   administrators can block, limit, or mark the app as trusted for their
   organization. This is outside dojo's control.
8. **100-user cap in Testing mode.** If the OAuth consent screen is set to
   Testing rather than Published, only 100 test users can grant access. Verify
   the publishing status before submission.
