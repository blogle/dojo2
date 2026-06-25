# dojo onboarding screen mockups

This bundle contains the curated, spec-aligned onboarding mockup screens generated for implementation reference.

## Contents

1. `01-onboarding-choice.png` — First-run pre-application choice screen with `Start empty` and `Migrate from Aspire` paths.
2. `02-aspire-migration-form.png` — Aspire migration form requesting only the Google Sheet ID with `Submit` and `Cancel` actions.
3. `03-migration-progress.png` — Blocking migration progress screen after Google authorization succeeds.
4. `04-migration-complete.png` — Successful migration completion screen with `Details` and `Continue to app` actions.
5. `05-import-details-modal.png` — Import details modal with record counts, validation summary, and non-blocking warnings.
6. `06-invalid-sheet-id-error.png` — Migration form failure state for invalid or missing Google Sheet ID.
7. `07-google-authorization-denied.png` — Migration form failure state after Google authorization is denied or fails.

## Implementation notes

- Onboarding is a pre-application surface and does not use the normal in-app navigation rail.
- Keep the layout centered, low-friction, and lightweight; this is not a guided setup wizard.
- Canonical labels: `Start empty`, `Migrate from Aspire`, `Submit`, `Cancel`, `Details`, `Continue to app`.
- The migration input expects a Google Sheet ID only.
