# Make financial mutations durable, conflict-safe, and recoverable

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must remain current as implementation proceeds.

The repository does not contain a root `PLANS.md`; this document follows the ExecPlan conventions used by the other files in `docs/plans/`.

## Purpose / Big Picture

After this work, every visible Budget and Transactions action either persists and reports success or retains the user's input and reports failure. Reviewed Aspire imports pass the same aggregate validation as direct imports before replacing financial data. Concurrent browser edits cannot silently overwrite newer transaction versions. Production DuckDB data has both fast OpenEBS ZFS recovery points and encrypted, rotating Google Drive backups, with restoration rehearsed against a new persistent volume before promotion.

The result is observable by refreshing after budget operations, forcing failed and stale transaction mutations, comparing direct and reviewed Aspire validation reports, and completing a backup-to-new-PVC restore rehearsal.

## Progress

- [x] (2026-09-03) Traced the affected frontend, API, SCD2, import, migration, deployment, and test paths.
- [x] (2026-09-03) Agreed to OpenEBS ZFS snapshots for local recovery and encrypted Google Drive backups authenticated by a service account.
- [x] (2026-09-03) Agreed that scheduled backups must not stop the application; they will back up a temporary PVC restored from a CSI snapshot.
- [x] (2026-09-03) Milestone 1: added explicit API errors, success-only transaction UI transitions, SCD2 row versions, conditional update/delete, and stale-write HTTP 409 behavior.
- [x] (2026-09-03) Milestone 2: rewired move and group funding to idempotent allocation commands, fixed creation order payloads and hidden-category restoration data, and made Save persist hierarchy changes while Cancel restores persisted state.
- [x] (2026-09-03) Milestone 3: added complete reviewed-decision parsing, aggregate validation inside the candidate transaction, conditional draft consumption, validation-aware UI completion, and passing direct/reviewed fixture rehearsals.
- [x] (2026-09-03) Milestone 4: implemented manifest-bearing DuckDB recovery, checkpoint, hash verification, non-overwriting restore commands, launchers, and focused tests.
- [x] (2026-09-03) Milestone 5 implementation: added OpenEBS snapshot orchestration, temporary-PVC recovery, encrypted Google Drive restic rotation, pre-migration backup gating, and a new-PVC restore Job template. Cluster discovery and a real restore rehearsal remain operational acceptance work.
- [ ] Update durable documentation and pass the complete repository gate (completed: architecture, decision, contribution, changelog, and operator docs; remaining: final test, image, and E2E gates).

## Surprises & Discoveries

- Observation: Budget move and group-funding handlers submit derived fields that the category update API forbids, then close their modals before the requests finish.
  Evidence: `web/src/dojo/pages/BudgetsPage.vue` submits `available_minor` and `monthly_funding_minor`, while `api/src/dojo/api/models.py::CategoryUpdatePayload` sets `extra="forbid"` and defines neither field.

- Observation: Save and Cancel in reordering mode invoke the same function, and Save performs no persistence.
  Evidence: `web/src/dojo/pages/BudgetsPage.vue` binds both events to `toggleReorder`.

- Observation: The reviewed import commits replacement data without `_validate_bundle()`, while the completion page says validation succeeded.
  Evidence: `api/src/dojo/service.py::commit_import_draft` clears and inserts at lines 1020-1034 without the call present in `_apply_import_bundle`; `web/src/dojo/pages/OnboardingPage.vue` advances on any resolved HTTP response.

- Observation: SCD2 physical `row_id` is already a unique transaction version token, so optimistic concurrency needs no schema migration.
  Evidence: `api/src/dojo/sql/schema/current.sql` stores one UUID `row_id` per physical version and `api/src/dojo/scd.py` creates a new row ID on replacement.

- Observation: A live-file copy is not an acceptable scheduled DuckDB backup, but an OpenEBS CSI snapshot can provide a no-downtime crash-consistent source that is recovered and verified on a temporary PVC before upload.
  Evidence: the application owns one open DuckDB connection, and the production PVC is currently the only durable copy.

- Observation: Aggregate validation exposed an existing reviewed-import collision when a user explicitly imported a tracking account with the same name as a budget account.
  Evidence: the first reviewed validation rehearsal failed account visibility checks for `Wallet`; reviewed tracking accounts now receive a deterministic ` (tracking)` suffix only on an actual name collision.

- Observation: Both direct and reviewed fixture paths validate 210 aggregate checks with zero failures against the current code.
  Evidence: `just validate-aggregates-fixture` and `just validate-reviewed-aggregates-fixture` completed successfully on 2026-09-03.

## Decision Log

- Decision: Use SCD2 `row_id` as an opaque API `version`, require it for transaction update and delete, and compare it atomically while closing the current version.
  Rationale: UUID row IDs already change on every edit and remain reliable when timestamps tie, avoiding a persistence migration.
  Date/Author: 2026-09-03 / product owner and opencode

- Decision: Group funding is planned and committed server-side as one idempotent command.
  Rationale: The product's “partial” rule describes distribution when Available to budget runs out; separate HTTP mutations would expose partially failed and stale client-side plans.
  Date/Author: 2026-09-03 / opencode

- Decision: Reordering keeps one complete browser draft and persists dense group/category order and parent updates through the existing typed SCD2 APIs, with Save and Cancel separated and failures kept visible.
  Rationale: The reported release blocker is that Save performs no persistence at all. Reusing the existing configuration APIs is the smallest correction; a future batch command can add all-or-nothing hierarchy concurrency if operational evidence requires it.
  Date/Author: 2026-09-03 / opencode

- Decision: Reviewed import validation runs after candidate insertion but before commit; failed-run auditing is written after rollback.
  Rationale: Aggregate validation reads the candidate database state, while failure evidence must survive candidate rollback.
  Date/Author: 2026-09-03 / opencode

- Decision: Scheduled backups use OpenEBS ZFS CSI snapshots without application downtime, then restore to a temporary PVC for DuckDB recovery, verification, and encrypted upload through restic and rclone to Google Drive.
  Rationale: Local snapshots are fast but share the cluster failure domain; Google Drive is off-site, and restic supplies encryption, retention, deduplication, and integrity checks.
  Date/Author: 2026-09-03 / product owner and opencode

- Decision: Restoration always targets a new PVC and is promoted only after migration and API-level verification.
  Rationale: Overwriting the only production volume would destroy the fastest rollback path.
  Date/Author: 2026-09-03 / opencode

## Outcomes & Retrospective

The application safety paths and deployment resources are implemented. `just check` passes; its evidence includes 78 backend integration tests, 16 property tests, 275 frontend tests, backup/unit coverage, architecture checks, type checking, linting, builds, and documentation. Kubernetes manifests render and both fixture import rehearsals pass. The existing AL-07 tracking-cutover browser scenario still fails its `Variance: $0.00` assertion on two runs; the other six E2E scenarios pass. The container build is blocked because Nix excludes newly created untracked files from the flake source until they are tracked. Cluster discovery and a real restore rehearsal also require the production OpenEBS context and Google Drive credentials. No secret material belongs in this repository.

## Context and Orientation

The Vue frontend in `web/src/dojo/` calls FastAPI routes in `api/src/dojo/api/routes.py` through `web/src/dojo/api/client.ts`. `api/src/dojo/service.py` owns domain operations and uses `api/src/dojo/database.py` for one serialized DuckDB connection. Editable records use slowly changing dimension type 2 (SCD2): an edit closes the current physical row and inserts a new row with the same logical ID and a new `row_id`.

Budget balances are derived. Moving or funding money must create allocation records rather than mutate category response fields. Category and group configuration is SCD2 state. The reviewed Aspire flow stores a pending import draft, accepts review decisions, transforms a parsed bundle, then replaces domain tables. Aggregate validation in `api/src/dojo/aggregate_validation.py` compares the inserted candidate state with source-derived expectations.

Production runs one pod with `Recreate` rollout against PVC `dojo-data`. `deploy/k8s/base/deployment.yaml` runs `dojo-migrate` before the API but has no backup gate. The target cluster uses OpenEBS ZFS; exact installed StorageClass and VolumeSnapshotClass names must be discovered before binding the production overlay. Google Drive access will use a service account and a narrowly shared folder. The restic repository password and service-account key are independent Kubernetes Secrets and must be recoverable outside the cluster.

## Plan of Work

Milestone 1 introduces an `ApiError` frontend boundary, success-only transaction UI transitions, and a conditional SCD2 replacement operation. Transaction reads expose `version`; update and delete require `expected_version`; stale requests return HTTP 409 with a stable code. All frontend call sites, including account detail and legacy state wrappers, must carry the observed version. Tests prove one of two concurrent edits wins, stale changes preserve the winner and reconciliation state, and failed mutations retain drafts and do not create undo entries or success toasts.

Milestone 2 replaces weak budget payloads with explicit TypeScript and Pydantic contracts. Move funds becomes an idempotent allocation command. Group funding becomes a server-side plan plus one transactional command following `SPEC.md` priority and capping rules. New group/category order values are bounded and dense. Retired categories use a dedicated hidden-inclusive query. Reorder mode owns a complete draft hierarchy; Save persists dense group/category order and cross-group parent changes through existing SCD2 APIs, while Cancel restores persisted props. Modals close and clear only after success.

Milestone 3 parses review decisions into one complete semantic decision set before mutation. A successful reviewed commit conditionally consumes the pending draft, inserts the transformed bundle, runs `_validate_bundle`, inserts the import batch, and marks the draft committed in one transaction. A validation exception rolls candidate data back and records a failed import run separately. The API returns the validation report. The web accepts completion only when `ok` and `validation_report.passed` are true. A new reviewed-import validation CLI path runs the fixture and saved fetch dump through analyze/commit and compares its aggregate results with direct import.

Milestone 4 adds focused backup and restore modules with CLI launchers and tests. They produce and verify manifests containing hashes, DuckDB/runtime identity, image digest, source snapshot/PVC, timestamps, and row/invariant summaries. restic provides encrypted snapshots and retention; rclone transports them to a service-account-accessible Google Drive folder. Commands never copy a database that is still owned by the live application.

Milestone 5 first discovers the cluster's OpenEBS ZFS StorageClass, VolumeSnapshotClass, CSI driver, and snapshot-controller support. The scheduled workflow creates a CSI snapshot, restores it to a uniquely named temporary PVC, opens and checkpoints that clone with the matching DuckDB runtime, verifies it, uploads it, verifies the remote restic snapshot, and then cleans temporary resources. Planned deployment waits for a verified off-site backup after the old pod stops and before migration. Restore materializes an explicit backup ID onto a new PVC, verifies and migrates a clone, runs an isolated API smoke comparison, and only then changes the production claim reference.

## Concrete Steps

Work from the repository root `/home/ogle/src/dojo2`. Use root `just` recipes whenever they exist. Add narrow recipes only where backup, restore, manifest rendering, or reviewed-import rehearsal currently has no canonical entrypoint.

After each backend slice run `just test-integration`, `just test-property` when financial invariants changed, `just lint-api`, `just typecheck`, and `just architecture-check`. After each frontend slice run `just test-web`, `just lint-web`, and `just typecheck`. After deployment changes run the new manifest validation recipe and `just container`. At completion run `just check`, `just test-e2e`, and `just container`.

## Validation and Acceptance

Budget acceptance requires move, group funding, creation, reorder Save/Cancel, and retired restore to survive browser refresh. Retry of the same move or group operation creates one financial effect. Group funding follows due-date, goal-kind, and table-order priority and never makes Available to budget negative. Reorder failures remain visible instead of reporting success.

Transaction acceptance requires a failed create to retain every draft field, success to reset only the intended fields, and update/delete failures to create no undo or success UI. Two clients editing version A must produce one success and one 409; the winner remains current with one historical predecessor.

Import acceptance requires direct and reviewed fixture/dump rehearsals to return passing validation reports and matching financial aggregates. Forced reviewed validation failure must preserve prior data, leave the draft pending, and retain a failed import-run record. Completion copy appears only for a passing report.

Recovery acceptance requires a scheduled no-downtime CSI snapshot to become a verified encrypted Drive backup, and a chosen Drive backup to restore onto a new PVC, migrate, start an isolated API, and reproduce representative financial and SCD2 results. The old PVC remains untouched. A failed pre-migration backup must prevent migration.

## Idempotence and Recovery

Financial commands use stable client operation IDs and request fingerprints, so identical retries replay one result while conflicting reuse is rejected. Candidate import and hierarchy mutations are transactional. Failed validation leaves prior domain state intact. Backup uploads are addressed by restic snapshot identity; retention runs only after a successful upload and verification. Kubernetes temporary resources use unique labels and can be safely discovered and removed after failed runs. Restore and rehearsal refuse to write into the production PVC or a nonempty destination.

## Artifacts and Notes

Keep short evidence in this plan as work proceeds: focused test names and counts, direct/reviewed validation summaries, rendered snapshot class/driver discovery, restic snapshot IDs, and restore rehearsal timings. Never record credentials, OAuth tokens, service-account JSON, or the restic password.

## Interfaces and Dependencies

The final transaction API exposes `version: string` on each transaction. Update bodies contain the normal editable fields plus `expected_version: string`; delete carries the expected version explicitly. Stale responses use HTTP 409 and a stable machine code.

Move and group-funding requests contain UUID `client_operation_id` values and return command results suitable for exact replay. Group funding returns ordered fully funded, partially funded, and unfunded category summaries. Reorder requests contain a full ordered user hierarchy and expected versions, not relative drag instructions.

The backup image contains the existing DuckDB runtime plus restic and rclone. Kubernetes Secrets provide rclone service-account configuration and the restic password. The production overlay binds discovered OpenEBS class names rather than assuming the cluster default. Root `just` recipes remain the operator-facing interface.

Revision note (2026-09-03): Updated after implementing all five milestones. Recorded the tracking-name collision found by reviewed validation, exact passing checks so far, and the cluster-dependent rehearsal that cannot be completed without production credentials and an OpenEBS context.

Revision note (2026-09-03): Final verification update records the passing `just check`, the pre-existing AL-07 browser assertion failure, the untracked-file Nix limitation, and the intentionally incremental reorder persistence decision.
