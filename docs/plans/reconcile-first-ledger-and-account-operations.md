# Deliver a reconcile-first ledger with optional transfer provenance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must remain current as implementation proceeds.

The repository does not contain a root `PLANS.md`; this document follows the ExecPlan conventions used by the other files in `docs/plans/`.

## Purpose / Big Picture

After this work, category funding persists correctly, tracking-account upgrades land on their newly created account, and dojo has a coherent pre-release accounting model that preserves Aspire's row-oriented ledger while adding safer account-specific operations. The Transactions page remains a transparent view of every current ledger row. Users may enter individual budget or investment transfer legs manually, while richer account-detail actions such as investment contribution, investment withdrawal, and credit-card payment create both legs atomically and record optional counterparty provenance.

Transfer provenance is explanatory metadata, not a financial input. Account balances, Available to budget, category activity, investment value, credit-card payment reserves, and net worth derive from transaction rows, account classes, system categories, account-budget links, allocations, and statement evidence. Imported Aspire rows do not need to be paired during onboarding. Future tooling may help users recover historical counterparties without rewriting transaction contents or changing financial results.

The application is not considered MVP-ready until account-local reconciliation exists. Reconciliation must cheaply compare one account's current ledger with an external statement, persist exactly which transaction versions were verified, surface missing or changed rows, and reopen the account when previously verified financial content changes. It must not require global transfer matching.

## Progress

- [x] (2026-08-21) Traced funding, investment contribution, loan payment, transaction entry, transfer, cutover, account-value, and category derivation paths.
- [x] (2026-08-21) Confirmed that category funding currently submits a derived `available_minor` field through category configuration instead of creating an allocation.
- [x] (2026-08-21) Confirmed that tracking cutover succeeds but leaves the browser routed to the retired predecessor account.
- [x] (2026-08-21) Agreed on a row-oriented ledger, optional non-financial provenance, account-detail rich operations, and account-local reconciliation.
- [x] (2026-08-21) Agreed that investment contribution shortfalls are not automatically funded; budget correction remains a separate Budget-page operation.
- [x] (2026-08-21) Agreed that pending transfer legs may settle on different dates and statuses, and pending investment contributions consume their linked category on entry.
- [x] (2026-08-21) Agreed to exclude investment-to-investment transfers from the MVP.
- [x] (2026-08-21) Reviewed this plan twice, corrected recovery and concurrency gaps, and verified it with `git diff --check` and `just docs`.
- [x] (2026-08-21) Milestone 1: added the fresh-schema command receipt and operation-provenance foundation, canonical fingerprints, JSON-stable replay, SCD2 link/relink/unlink, singleton and separate-connection concurrency coverage, and financial-invariance proof.
- [x] (2026-08-21) Milestone 2: replaced derived category mutation with idempotent semantic funding, active allocatable-category validation, negative-ATB persistence, success-only modal close, retry-stable operation identity, and focused backend/component coverage.
- [x] (2026-08-29) Milestone 3: added exact contemporary cutover reconciliation, required average cost, dated unrealized gain calculations, idempotent cutover, and correct successor navigation.
- [x] (2026-08-29) Milestone 4: added unified budget/investment ledger entry, strict new-entry combinations, transfer event ordering, link-independent ATB, all/spending/transfer views, and hard-cut removal of `transactions.transfer_id`.
- [x] (2026-08-21) Milestone 5: added receipt-backed investment contribution/withdrawal and credit-card payment operations with independent leg evidence, no auto-funding, operation provenance reads, and account-detail controls.
- [x] (2026-08-21) Milestone 6: implemented account-local reconciliation evidence, working sets, digest-checked correction flow, reopening status, and a balance-first budget-account action.
- [x] (2026-08-21) Milestone 6 verification: migration, integration (70 tests), property (16 tests), frontend (272 tests), lint, formatting, typecheck, and architecture checks pass; focused reconciliation tests cover comparison, explicit adjustment, and reopening.
- [x] (2026-08-29) Milestone 7: rich operations expose operation-relation counterpart provenance while manual/imported rows remain truthfully unlinked; historical matching remains deferred.
- [x] (2026-08-29) Milestone 8: completed the repository gate, 74 backend integration tests, 16 property tests, 272 frontend tests, and seven browser scenarios. Cold E2E baseline generation exceeded budget; the immediate warm rerun passed every functional and performance budget.

## Surprises & Discoveries

- Observation: Funding appears successful because unknown `available_minor` input is silently discarded by `CategoryUpdatePayload`, after which the modal closes.
  Evidence: `web/src/dojo/pages/BudgetsPage.vue` calls `updateCategory` from `submitFundCategory`, while `api/src/dojo/api/models.py` does not define `available_minor` on category updates.

- Observation: Funding below zero Available to budget is intentional product behavior, not a validation failure.
  Evidence: `SPEC.md` says category funding succeeds when Available to budget becomes negative and leaves a persistent warning.

- Observation: Tracking cutover already returns ordered successor account IDs; the frontend ignores them.
  Evidence: `api/src/dojo/service.py::_tracking_cutover_response` returns `successor_account_ids`, and `web/src/dojo/api/client.ts::createTrackingCutover` types them, but `AccountDetailPage.vue` does not navigate in mutation success handling.

- Observation: Aspire transfer rows are imported as independent `TX_ACCOUNT_TRANSFER` transaction rows without reliable counterparty identity.
  Evidence: `api/src/dojo/importer.py` maps the system category but has no source transfer identifier; import persistence does not populate `transactions.transfer_id`.

- Observation: Most current financial calculations already use local transaction-leg facts rather than `transfer_id`.
  Evidence: account balances, investment provisional value, investment linked-category activity, and credit-card payment reserves select by account, sign, system category, date, and status. The current investment-withdrawal Available-to-budget exception is the notable financial dependency on `transfer_id`.

- Observation: Generic reconciliation persistence and the specified changes-since-reconciliation working set do not yet exist.
  Evidence: `SPEC.md` defines the behavior, while current budget reconciliation controls are stubs and only investment/loan/tracking-specific statement or snapshot records are persisted.

- Observation: Current transaction edits, deletes, and restores operate on one leg even when a `transfer_id` is present.
  Evidence: `api/src/dojo/service.py::update_transaction`, `delete_transaction`, and `restore_transaction` are transaction-ID scoped and preserve rather than validate transfer metadata.

- Observation: Existing rich financial POST operations are not idempotent.
  Evidence: generic transaction and transfer services generate new UUIDs on every request; a retry can duplicate rows and investment shortfall allocations.

- Observation: Physically removing `transactions.transfer_id` in Milestone 1 would force the link-independent ATB and transaction-presentation cutover to happen before their Milestone 4 tests exist.
  Evidence: current ATB and counterparty readers still query `transfer_id`. Milestone 1 therefore adds the new operation/receipt foundation without using it financially; Milestone 4 removes the legacy column and readers in the same fresh-schema change that proves link-independent behavior.

- Observation: DuckDB can allow two separate connections to begin the same idempotent command before either receipt is visible.
  Evidence: Milestone 1's separate-connection concurrency test forces both mutations to start. The losing transaction rolls back on the write conflict, waits for the winning receipt, and returns the committed JSON-stable result; one receipt and one financial effect remain.

- Observation: Provenance SCD invariants rely on dojo's documented singleton writer for normal operation, while receipt identity also has a database primary key and cross-connection recovery.
  Evidence: `Database.transaction()` serializes one application connection. Operation helpers validate one current relation per transaction and one role per operation; operation relations are non-financial and are changed only through that writer boundary.

- Observation: Resetting a funding modal draft when Save is clicked defeats idempotent retry even when the backend is correct.
  Evidence: the first funding implementation cleared custom amount immediately after emit. Milestone 2 now resets only when the modal closes, and a component test proves a failed request retries with the same operation ID and amount.

- Observation: Ending-balance reconciliation must separate statement-period matching from the all-history balance equation.
  Evidence: final review found that summing only rows after `period_start` omits opening history. Draft/apply baselines now cover all current rows through cutoff while source classifications remain period-bounded; investment ending value uses holdings plus cash and cleared provisional transfers.

- Observation: E2E baseline-generation performance is sensitive to cold cache state while scenario execution remains stable.
  Evidence: final cold generation took 3.95 seconds against a 3.0-second budget and all seven scenarios passed. The immediate warm run generated in 0.94 seconds and passed every functional and performance budget.

- Observation: The working tree contained unrelated onboarding, OAuth, import, and frontend proxy edits before this plan was created.
  Evidence: `git status --short` on 2026-08-21 listed `CHANGELOG.md`, `api/src/dojo/api/routes.py`, `api/src/dojo/google.py`, `api/src/dojo/importer.py`, `api/tests/test_api_endpoints.py`, `api/tests/test_google.py`, `api/tests/test_importer.py`, `web/src/dojo/api/client.ts`, `web/src/dojo/pages/OnboardingPage.vue`, `web/src/dojo/state/app.ts`, `web/src/dojo/types.ts`, `web/tests/App.test.ts`, `web/vite.config.ts`, and untracked `tmp/`. Those changes must not be staged, reformatted, overwritten, or deleted by this work unless their owner explicitly integrates them later.

- Observation: The existing investment statement status is specialized source-of-truth evidence and must not be replaced by an empty generic reconciliation history.
  Evidence: The account-value integration test expects an investment with a statement and no provisional transfers to remain `CURRENT`; generic reconciliation status is overlaid only when a generic commit exists or the account is reopened.

- Observation: The account-local MVP accepts and classifies normalized source records through the backend while the first account-detail action remains balance-first.
  Evidence: The draft endpoint persists source evidence and returns exact/source-only/local-only/duplicate/mismatch classifications; the modal intentionally submits no source records and explains that the API contract is available for richer clients.

- Observation: Duplicate source identities must be retained as evidence rather than rejected by the evidence table.
  Evidence: The source-record primary key uses evidence ID plus upload ordinal; duplicate provider IDs are then classified by the pure comparison function.

## Decision Log

- Decision: Preserve Aspire's row-oriented transaction model. Manual transfer legs created through Transactions are valid independent rows and need not carry counterparty provenance.
  Rationale: Aspire does not provide reliable pairing identity, and mandatory pairing would create an expensive and error-prone migration gate.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Keep Transactions as the default all-current-rows ledger view. Add optional `Spending & income` and `Transfers` filters without hiding transfers by default.
  Rationale: Bank and credit-card statement entries must remain visible in the consolidated ledger; optional views make operating metrics useful without concealing source records.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Permit active budget and investment accounts in manual entry only for domain-valid combinations. Investment accounts accept only account-transfer entries; normal budget categories remain budget-account-only.
  Rationale: Investment transfer legs must be manually representable, but categorized investment transactions conflict with the holdings-plus-cash source of truth.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Transfer provenance is optional, SCD2-versioned explanatory metadata and has no financial effect.
  Rationale: Users benefit from known source/destination flows, but linking, unlinking, and relinking historical rows must never alter balances, budgets, net worth, or reconciliation state.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Use a hard pre-release cutover to the new operation/provenance schema instead of dual-reading the current `transactions.transfer_id` representation.
  Rationale: There are no released databases to preserve. Rebuilding from Aspire avoids two relationship authorities and compatibility complexity.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Account-detail rich operations create both transaction legs and optional provenance atomically and idempotently.
  Rationale: These surfaces promise better previews and guardrails than manual row entry; retries must not duplicate financial movement.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Investment contribution shortfalls are not automatically funded.
  Rationale: Budget assignment and operational spending remain separate decisions. A contribution may make its linked category negative, after which the user funds or covers it on the Budget page.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Pending investment contributions consume linked-category availability on entry, while only cleared investment legs alter authoritative/provisional investment value.
  Rationale: The category reserves the commitment immediately, while institution settlement may occur several days later on each account independently.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Linked legs may have different posting dates and settlement statuses.
  Rationale: Real transfers can clear in the source account before posting in the destination account. Provenance identifies one intended movement but does not collapse account-local settlement evidence.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Intended transfers are 1:1 equal-and-opposite financial movements. Interest, fees, and unexplained differences are separate categorized or balance-adjustment records.
  Rationale: This keeps transfer semantics simple and aligns with the existing Aspire ledger.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Investment-to-investment transfers are outside the MVP.
  Rationale: Link-independent account/sign algebra cannot distinguish them from budget-boundary contributions without an additional explicit treatment.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Reconciliation is account-local and does not require counterparty matching.
  Rationale: One account can be verified cheaply against its own statement even when another account remains pending or incorrect. Global matching would turn routine reconciliation into an expensive historical investigation.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Provenance matching is not part of the reconciliation MVP.
  Rationale: Reconciliation establishes local financial correctness. Historical flow recovery is optional enrichment and can be implemented later without blocking regular commits.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Reconciliation and provenance tooling do not directly edit transaction contents. Financial corrections continue through explicit SCD2 transaction commands.
  Rationale: Relationship review must not silently rewrite amounts, dates, accounts, statuses, categories, or historical balances.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Use the existing `financial_command_receipts` command boundary for reconciliation apply idempotency instead of adding a separate apply ledger.
  Rationale: Apply is the only reconciliation operation that may create money. Reusing the existing receipt table gives exact retry/conflict behavior while keeping reconciliation evidence immutable and the schema minimal.
  Date/Author: 2026-08-21 / opencode

- Decision: Ship a truthful balance-first account-detail action and keep source-record decision editing out of this milestone.
  Rationale: The backend contract, persisted evidence, classification, stale-draft protection, and explicit adjustment path are release-critical. A partial source-review editor would imply decisions it cannot persist safely; the modal instead previews the balance and requires an explicit adjustment choice.
  Date/Author: 2026-08-21 / opencode

- Decision: Tracking cutover requires an explicitly entered same-date final tracking value that exactly equals the signed successor opening total.
  Rationale: Cash and holdings are independent user inputs. A contemporary source snapshot eliminates time-delta ambiguity and prevents the representation change from creating a net-worth jump.
  Date/Author: 2026-08-21 / product owner and opencode

- Decision: Investment holdings require quantity, price per unit as of the statement/cutover date, and average cost per unit.
  Rationale: Price values the position; average cost supports current-scope unrealized gain/loss and future performance work.
  Date/Author: 2026-08-21 / product owner and opencode

## Outcomes & Retrospective

Milestones 1–8 are implemented and verified in the current worktree. Category funding persists allocations; tracking cutover records exact same-date evidence and routes to successors; manual and imported transfer legs remain first-class financial rows; rich investment and credit-card actions add optional operation provenance; and account-local reconciliation persists source evidence, all-history ending-balance baselines through cutoff, exact transaction versions, explicit adjustments, and reopening state. The fresh schema no longer contains `transactions.transfer_id`, so provenance has one canonical non-financial representation. Investment statement evidence remains authoritative when no generic commit exists, and generic investment drafts compare ending value against holdings plus cash and cleared provisional transfers. The remaining deliberate gap is a rich source-record decision UI and optional historical counterpart matcher; the current modal is a truthful balance-first path, while backend source-record comparison is available and tested. Cold E2E baseline generation remains an environmental performance sensitivity documented above.

## Context and Orientation

The FastAPI and DuckDB backend lives in `api/src/dojo/`. HTTP request parsing belongs in `api/src/dojo/api/models.py` and `api/src/dojo/api/routes.py`. Domain workflows and persistence orchestration currently live in `api/src/dojo/service.py`. SQL resources live under `api/src/dojo/sql/`. Financial records use slowly changing dimension type 2, abbreviated SCD2: editing closes the current database row and inserts a replacement with the same logical identity, preserving what dojo previously knew.

The Vue 3 frontend lives in `web/src/dojo/`. The relevant pages are `pages/BudgetsPage.vue`, `pages/TransactionsPage.vue`, and `pages/AccountDetailPage.vue`. API calls are in `api/client.ts`; domain-shaped frontend types are in `types.ts`. The transaction entry and ledger components are `components/transactions/TransactionEntryForm.vue` and `TransactionLedger.vue`. Cypress component tests live in `web/cypress/component/`, and browser acceptance tests live in `web/cypress/e2e/`.

An ordinary transaction row is one account-local financial fact. A transfer leg is a transaction whose system category is `TX_ACCOUNT_TRANSFER`; the sign indicates inflow or outflow for that account. An operation is optional metadata that explains how two known legs were created together. A reconciliation commit is evidence that one account's specific current transaction versions agreed with an external source through a cutoff date.

The supported MVP transfer boundaries are budget deposit or credit-card accounts to other budget accounts, and budget deposit accounts to or from investment accounts. Tracking accounts, loans, and tangible assets do not accept transfer legs. Loan payment is one categorized budget-account transaction plus loan attribution. Investment-to-investment transfers are intentionally rejected until separately specified.

## Plan of Work

### Milestone 1: Establish financial commands and optional provenance

Implement the new schema and idempotent command boundary before changing any composite or money-moving workflow. Because the application is pre-release, the checked-in schema and tests target a fresh database rather than supporting the current local `transactions.transfer_id` representation. Introduce an operation header and SCD2 operation-leg relationship keyed by logical transaction IDs. The operation records kind, origin, client operation ID, request fingerprint, and creation metadata. The leg relation records operation, logical transaction, and source/destination role. Manual and imported transactions have no operation relation. Rich actions create operation and legs atomically.

Use a `financial_command_receipts` table for idempotency. Its minimum fields are client operation UUID primary key, command kind, SHA-256 request fingerprint, serialized successful result, and creation timestamp. The primary key is the database-enforced concurrency boundary. The service checks for an existing receipt inside the same DuckDB transaction used by the command. Repeating the same operation ID and fingerprint returns the stored result. Reusing the ID with a different fingerprint raises a conflict before any mutation. Insert the receipt only after all financial rows and operation relations have been inserted successfully, in the same transaction. Concurrent same-ID requests are serialized through the repository's single writer boundary; if a uniqueness conflict is still observed, roll back the losing transaction, reread the committed receipt, and return it only when its fingerprint matches. Add a concurrent two-caller test proving one financial effect and one stored result.

Do not use operation or receipt tables from financial read SQL. Add architecture and behavior tests that compare every financial aggregate before and after link, unlink, and relink operations. The values must remain identical. Delay historical matcher implementation; expose only relation reads needed for rich actions and later UI.

This milestone is complete when a fresh schema provisions, a toy two-leg operation and relation can be inserted atomically, retry tests prove one result, conflicting retry tests prove no mutation, and provenance invariance tests pass. Run `just migration-check`, `just test-integration`, `just test-property`, `just lint-api`, `just typecheck`, and `just architecture-check`.

### Milestone 2: Persist real category funding

Replace the false category-configuration update with a domain-shaped funding command. Add a request model for funding a category by `category_id`, date, positive amount, and memo. The service resolves the Available-to-budget system bucket and category bucket, verifies an active allocatable standard category, and inserts one allocation. The client no longer supplies internal system-bucket IDs. Funding remains valid when it makes Available to budget negative.

In `BudgetsPage.vue`, add a dedicated mutation that calls this endpoint, invalidates budget and allocation queries, and closes the funding modal only after success. Configure category-update parsing to reject unknown fields so future attempts to mutate derived balances fail visibly. Add frontend coverage for the exact Fund, Custom amount, 1000, Save sequence and backend integration coverage proving category availability, monthly Budgeted, ATB, and funding history after reload.

The funding request carries a required client operation ID and uses the receipt behavior from Milestone 1. Name focused tests so their intent is recoverable, including `test_fund_category_persists_allocation_and_allows_negative_atb`, `test_fund_category_retry_is_idempotent`, and a Budgets-page component case that asserts `POST /api/allocations/fund` rather than `PUT /api/categories/{id}`. Run `just test-integration`, `just test-web`, `just lint`, `just typecheck`, and `just architecture-check`.

### Milestone 3: Make tracking cutover truthful and navigable

Extend the cutover request with a required positive `final_predecessor_value_minor` while retaining the expected predecessor value as an optimistic concurrency check. Remove the confirmed-variance escape hatch. In the same DuckDB transaction, correct or create the predecessor snapshot on the cutover date, require its signed value to equal the combined signed successor openings exactly, create successors, record replacement relations, and retire the predecessor from current views.

The cutover UI starts the final tracking value blank so the user must enter contemporary evidence. Investment holdings add required average cost per unit and rename price to `Price per unit on cutover date`. Statement reconciliation uses `Statement price per unit` and `Average cost per unit`. Add pure calculations for total cost basis and dated unrealized gain/loss; do not add market-data pricing or broad period performance in this milestone.

Consume `successor_account_ids` after cutover. Route a current single-successor cutover to that successor's detail page, a current multi-successor cutover to Assets & Liabilities, and a future cutover back to the still-current predecessor with confirmation. Add investment, loan, multi-successor, future-date, mismatch rollback, basis, and navigation tests.

Holding arithmetic is exact integer arithmetic in minor units. For each holding, `value_minor = (quantity_micros * price_minor + 500_000) // 1_000_000`; `cost_basis_minor` uses the same formula with average cost per unit; `unrealized_gain_minor = value_minor - cost_basis_minor`. Account totals sum the rounded holding values and bases. Percentage gain is unavailable when total basis is zero.

Cutover uses the Milestone 1 client operation ID and receipt. Focused backend tests cover an identical retry, conflicting retry, exact final-value equality, transaction rollback on mismatch, and required basis. Frontend tests cover current single-investment, current single-loan, multi-successor, and future-date navigation. Run `just test-integration`, `just test-web`, `just test-e2e-spec web/cypress/e2e/assets-liabilities.cy.ts`, `just lint`, `just typecheck`, and `just architecture-check`.

### Milestone 4: Implement the unified ledger and link-independent calculations

Represent the entry category as a typed frontend union rather than a magic display string. New-entry combinations are:

    budget account + standard category -> ordinary categorized transaction
    budget account + Available to budget -> income/system transaction
    budget or investment account + Account transfer -> one unlinked transfer leg

Investment accounts cannot use standard categories. Tracking, loan, and tangible accounts are absent from new-entry account options. Starting balance remains creation/import behavior, and balance adjustment is available only from reconciliation. Historical editing always preserves and displays the row's current stored option, even when that option is not offered for new entry.

Transactions defaults to all current rows. Add an activity filter with `All activity`, `Spending & income`, and `Transfers`. All activity remains the default. Metrics are recomputed from the selected view and labeled so gross ledger flow is not mistaken for income or spending.

Every newly entered transfer leg receives a financial event order. Pending contribution legs consume the linked investment category immediately; only cleared investment legs affect investment provisional value. Dates and statuses remain leg-local.

Remove the financial dependency on provenance. Define and test the current supported-boundary Available-to-budget transfer adjustment as:

    sum(all current BUDGET account-transfer leg amounts)
    + sum(all positive current INVESTMENT account-transfer leg amounts)

The pure transfer-boundary function accepts only current transaction facts effective on or before the requested as-of date. Each fact contains logical transaction ID, account class, budget subtype when applicable, system category, signed minor-unit amount, date, and status. Both `PENDING` and `CLEARED` legs participate in ATB and linked-category reservation because budget commitment begins on entry; only investment valuation separately filters to `CLEARED`. Positive investment transfer legs create contribution activity; negative investment transfer legs do not. For complete valid rows the formula produces zero for budget-to-budget transfers, credit-card payments, and contributions, and the positive budget leg for investment withdrawals. Deleted/closed SCD2 versions and future-dated rows are excluded. Missing, duplicated, or mismatched current legs may temporarily produce residual ATB; users correct the underlying rows or add an explicit reconciliation adjustment, after which recomputation converges. Explicitly reject investment-to-investment and all other unsupported account-class transfer entry combinations.

Remove automatic investment shortfall funding from `create_investment_transfer`. Contribution preview shows linked-category availability and resulting negative availability but does not insert an allocation. Existing funding remains a separate Budget operation.

Add equivalence tests proving that complete manually entered unlinked legs and rich account-detail operations produce the same balances, ATB, category activity, investment value, and net worth. Their only difference is operation provenance and richer-flow validation.

Name focused tests for each algebra case: budget-to-budget, deposit-to-card, contribution, withdrawal, pending contribution, future-dated exclusion, deleted-leg exclusion, missing-leg residual, and investment-to-investment rejection. Add component tests for every new-entry account/category combination and for rendering a legacy current value that is not offered for creation. This milestone is complete when `just test-property`, `just test-integration`, `just test-web`, `just lint`, `just typecheck`, and `just architecture-check` pass.

### Milestone 5: Complete rich account-detail operations

Keep investment Contribute and Withdraw as recommended account-detail actions. They accept one positive amount and one budget deposit account, preview both resulting legs, linked-category impact, ATB impact, and net-worth neutrality, then atomically create both leg rows and operation provenance. The request contains `source_account_id`, `source_posted_date`, `source_status`, `destination_account_id`, `destination_posted_date`, `destination_status`, amount, memo, and client operation ID. Contribution requires budget deposit as source and investment as destination; withdrawal reverses those roles. The UI defaults both dates and statuses together but exposes destination posting evidence so users can represent a source leg clearing several days before the destination. They never fund a category automatically. They reject credit-card funding sources and unsupported destinations.

Add a credit-card Pay action to budget credit-card detail. It accepts a source budget deposit account, amount, source posted date/status, card posted date/status, memo, and client operation ID. It previews the checking outflow, card inflow, payment-category reserve effect, ATB neutrality, and net-worth neutrality, then atomically and idempotently creates both legs and operation provenance.

Operation provenance may connect legs with different final dates or statuses. The operation records intended flow; each transaction remains authoritative for its account-local posting and settlement state. Account detail shows known counterparties for rich operations and `Counterparty unavailable` for independent rows without treating the latter as invalid.

Focused tests prove independent dates/statuses, idempotent retry, conflicting retry, no automatic allocation, credit-card source rejection for investment, reserve behavior, manual-versus-rich equivalence, and account-detail provenance. Run `just test-integration`, `just test-property`, `just test-web`, the focused assets/liabilities browser spec, `just lint`, `just typecheck`, and `just architecture-check`.

### Milestone 6: Build account-local reconciliation

Add generic reconciliation evidence for budget deposit and credit-card accounts, and integrate it with existing investment statement evidence. `reconciliation_commits` stores reconciliation ID, account ID/class, source kind, period start/end, effective date, verified timestamp, state, source evidence ID, baseline digest, source ending balance/value, and creation metadata. `reconciliation_source_records` stores source evidence ID, stable source record ID, account ID, posted date, optional cleared date, signed amount, source status, description, normalized digest, and raw payload. `reconciliation_transaction_refs` stores reconciliation ID, logical transaction ID, verified SCD2 `valid_from`, account ID, and canonical row digest. `reconciliation_decisions` stores explicit source/local match or include/exclude/adjust decisions when review requires them.

The canonical transaction digest serializes, in stable key order, logical transaction ID, current `valid_from`, account ID, date, signed amount, status, category ID, system category, and memo. The baseline digest hashes the sorted transaction digests through the reconciliation cutoff plus relevant account-settings and account-budget-link version identities, source evidence ID/digest, account ID, and cutoff. Source records use provider identity when supplied; otherwise the upload receives a generated evidence-set UUID and stable per-upload ordinal. Descriptions and amounts are never treated as identity.

Starting a reconciliation selects one account, source kind, period cutoff, source ending balance or value, and optional normalized statement records. The server builds a bounded account-local working set. It includes current rows for that account through the cutoff that are absent from the latest references or whose `valid_from` differs, plus prior referenced transactions that no longer have a current row. Rows dated after the cutoff do not invalidate that commit unless a later edit moves them into the covered period. It classifies exact matches, suggested matches, source-only rows, local-only rows, duplicates, amount/date/status differences, edits after baseline, deletions, restorations, and remaining balance difference.

Source-record matching inside one account may use stable provider identity or user-confirmed suggestions. It does not search for a counterparty account and does not create provenance. Transfer structure may be shown as a non-blocking warning when rich operation metadata already exists.

Applying reconciliation re-reads the baseline digest, rejects stale drafts, applies explicit SCD2 corrections and any user-approved balance adjustment, verifies the resulting source difference, persists the commit and transaction-version references, and marks it current. Balance adjustments are explicit `TX_BALANCE_ADJUSTMENT` rows tied to reconciliation evidence; they are never inserted silently.

Any later edit, status change, deletion, or restoration of a referenced transaction reopens the affected account. The prior commit remains immutable history. Relevant account-configuration changes also reopen covered periods when they alter financial interpretation.

Budget accounts reconcile ledger sign to source statement sign. Credit-card source liabilities are normalized to ledger sign. Investment reconciliation continues to use holdings, dated prices, and cash, but must also compare statement cash activity so a missing contribution or withdrawal leg cannot be hidden solely by replacing the ending statement value. Cleared post-statement legs remain provisional; pending legs remain visible but non-authoritative.

The normal reconciliation path must be cheap: no global transfer scan, no mandatory provenance review, bounded account/date queries, paged source records, and incremental work since the last baseline. Add benchmarks using the existing 1K, 10K, and 100K transaction fixtures before setting final budgets.

Expose `POST /accounts/{account_id}/reconciliations/draft`, `GET /reconciliations/{reconciliation_id}`, `POST /reconciliations/{reconciliation_id}/apply`, `GET /accounts/{account_id}/reconciliations`, and `GET /accounts/{account_id}/reconciliation-working-set`. Focused tests cover exact match, missing/extra/duplicate rows, amount/date/status mismatch, source identity, stale digest rejection, balance adjustment, credit-card sign normalization, edit/delete/restore/status reopening, rows after cutoff, independent counterparty state, investment cash activity, and 100K-account-local benchmark shape. Run `just migration-check`, `just test-integration`, `just test-property`, `just test-web`, the focused reconciliation browser spec, `just lint`, `just typecheck`, and `just architecture-check`.

### Milestone 7: Expose provenance without historical matching

Read operation provenance from account detail and transaction responses. Known rich-operation legs show counterparty and operation kind. Unlinked manual/imported transfer legs show no inferred counterparty. Linkage state is distinct from reconciliation state and transaction source.

Do not implement heuristic historical matching in the MVP. Reserve future API and UI space for `Find counterpart`, but do not generate or persist suggestions until reconciliation is stable and benchmarked. A future matcher must require exact opposite amounts, distinct compatible accounts, no conflicting active relation, explicit user confirmation, ambiguity reporting, bounded server-side candidate generation, and SCD2 linkage history. It must remain financially inert.

This milestone is complete when linked rich operations and unlinked manual/imported rows render truthfully on Transactions and account detail, provenance edits leave financial aggregates unchanged, and `just test-integration`, `just test-web`, `just lint`, `just typecheck`, and `just architecture-check` pass.

### Milestone 8: Verify the integrated behavior

Add deterministic browser acceptance for category funding persistence, manual transfer-leg entry, rich investment operations without auto-funding, credit-card Pay, cutover redirect/reconciliation, all/spending/transfers ledger filters, account-local reconciliation, reopening after a historical edit, and manual-versus-rich financial equivalence.

Retain the accepted investment contribution and mortgage payment scenarios. Extend them rather than replacing their current provenance, budget-activity, and net-worth invariants. Run focused checks after each milestone and the full repository gate before completion.

## Concrete Steps

Run all commands from the repository root `/home/ogle/src/dojo2`. The root `justfile` is authoritative.

Before implementation, capture `git status --short` and compare it with the baseline paths listed in `Surprises & Discoveries`. Commit only this plan with path-scoped staging:

    git diff --check -- docs/plans/reconcile-first-ledger-and-account-operations.md
    git add -- docs/plans/reconcile-first-ledger-and-account-operations.md
    git diff --cached -- docs/plans/reconcile-first-ledger-and-account-operations.md
    git commit -m "docs: plan reconcile-first ledger"

Never use `git add .` or `git add -A` in this worktree. Untracked `tmp/` is outside this plan.

After backend-only milestones, run:

    just test-integration
    just test-property
    just lint-api
    just typecheck
    just architecture-check

After frontend milestones, run:

    just test-web
    just lint-web
    just typecheck

After schema changes, run:

    just migration-check
    just architecture-check

Run targeted browser scenarios with:

    just test-e2e-spec web/cypress/e2e/assets-liabilities.cy.ts

Add a focused reconciliation/transactions browser specification and run it through the same `just test-e2e-spec` recipe.

Before declaring completion, run:

    just check
    just test-e2e

Record command outcomes and any environmental blockers in `Progress` and `Surprises & Discoveries`.

## Validation and Acceptance

Category funding acceptance: with Available to budget at zero, funding Stonks or Mortgage by $1,000 creates one persisted allocation, increases category Available and monthly Budgeted by $1,000, changes Available to budget to -$1,000, displays the negative warning, and remains correct after reload. Funding history shows the allocation. No category configuration request contains `available_minor`.

Cutover acceptance: the user enters a final tracking value dated on the cutover date. The signed sum of cash, holdings valued at cutover price, tangible values, and loan obligations must equal it exactly. Investment holdings require quantity, price per unit, and average cost per unit. Applying a single current successor lands on its detail page; applying several lands on the overview. No transaction or allocation is created and net worth is unchanged.

Ledger acceptance: Transactions opens with all current rows, including credit-card payments and investment transfer legs. `Spending & income` excludes account-transfer legs; `Transfers` shows only them. Manual entry accepts valid budget and investment transfer legs and rejects categorized investment transactions and unsupported account classes. Historical imported rows remain visible and editable through their current representation.

Transfer-calculation acceptance: complete budget-to-budget transfers, credit-card payments, and investment contributions have zero ATB transfer effect. Complete investment withdrawals increase ATB by the amount returned to a budget account. Contributions consume linked-category availability on entry, including pending contributions. Investment provisional value changes only for cleared legs. Investment-to-investment transfers fail validation.

Rich-operation acceptance: investment Contribute/Withdraw and credit-card Pay create two equal-and-opposite rows once, even when the same idempotency key is retried. They add operation provenance, present both accounts on detail, and produce the same financial results as equivalent complete manual legs. Contributions do not create allocations or automatically fund shortfalls.

Provenance acceptance: creating, changing, or removing an operation relationship changes only provenance responses. Account balances, ATB, category activity and availability, investment value, credit-card reserve, net worth, transaction versions, and reconciliation state remain identical.

Reconciliation acceptance: a budget account can reconcile independently to source records and ending balance without identifying transfer counterparties. A missing local statement record, extra local row, duplicate, amount/date/status mismatch, or deleted prior row appears in the working set. Applying with zero difference records the exact transaction versions. Editing, deleting, restoring, or changing status on one verified row reopens only the affected account while preserving the prior commit. A credit-card liability uses correct sign normalization. An investment statement cannot conceal unexplained cash activity.

Performance acceptance: opening the incremental working set does not scan or serialize every account. Results are paged. Benchmarks cover at least 100,000 total transactions and record account-local draft, working-set, and apply durations before thresholds are finalized.

## Idempotence and Recovery

The pre-release schema transition is a hard rebuild, but implementation and verification must use fresh test databases and must not delete the current local database automatically. Preserve Aspire source material and regenerate into a separate path before swapping any local database. Fresh provisioning and repeated fixture imports must be deterministic.

Before a manual local cutover, stop `just api` and every other process that may hold or write the DuckDB file. Do not use filesystem copy while the service or another DuckDB client is running. After all clients are closed, identify the actual path using the same default as the `just api` recipe. From the repository root, back it up outside the workspace and leave the original in place:

    db_path="${DUCKDB_PATH:-api/.local/dojo.duckdb}"
    test -f "$db_path"
    cp -- "$db_path" "/tmp/opencode/dojo-pre-reconcile-ledger.duckdb"

Provision and validate the new schema against a different database path. Do not replace the original until fresh provisioning, Aspire import, aggregate validation, and focused browser acceptance pass. If validation fails, discard only the new database and restore service configuration to the untouched original. If a swap has already occurred, stop the service and copy `/tmp/opencode/dojo-pre-reconcile-ledger.duckdb` back to the configured path.

Every composite financial command uses a client operation ID and request fingerprint. Retrying identical content returns the first result. Conflicting content with the same ID fails before mutation. Financial rows, allocations, operation provenance, and idempotency records commit together.

Reconciliation drafts use an expected baseline digest. If any relevant row changes before Apply, the command fails without partial corrections and the user refreshes the draft. Applied reconciliation commits are immutable. Reopening creates new current state without erasing prior evidence.

Provenance changes are independently reversible through SCD2 relation versions and never require transaction rollback. Future historical matching can be disabled or its relation rows closed without affecting financial records.

If implementation encounters the unrelated pre-existing working-tree changes listed in `Surprises & Discoveries`, do not discard, stage, format, or rewrite them. Several required files already carry unrelated edits, especially `api/src/dojo/api/routes.py`, `api/tests/test_api_endpoints.py`, `web/src/dojo/api/client.ts`, `web/src/dojo/state/app.ts`, `web/src/dojo/types.ts`, and `CHANGELOG.md`. Inspect each file's existing diff before a patch, preserve those hunks, and stage only this plan or later task-owned hunks. Report any unavoidable conflict before proceeding.

## Artifacts and Notes

The canonical product decisions live in this plan until corresponding updates land in `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, and `CHANGELOG.md`. Each implemented milestone must update the durable document required by the repository update guide.

The current accepted browser scenarios in `docs/plans/assets-liabilities-browser-acceptance.md` remain regression constraints, especially AL-05 investment contribution, AL-06 linked loan payment, and AL-07 tracking cutover.

## Interfaces and Dependencies

Use existing FastAPI, Pydantic, DuckDB, Vue Query, Vue Router, and Cypress dependencies. Do not add an external transaction-matching, workflow, or reconciliation library.

The backend must expose domain-shaped request variants rather than raw string combinations. Python request boundaries use Pydantic literals or discriminated models. Core reconciliation comparison, holding valuation, unrealized-gain calculation, transfer-boundary calculation, and baseline digest construction should be pure functions. Database reads/writes, request handling, clock access, and query invalidation remain imperative shell code.

The frontend must use literal unions or discriminated objects for account class, entry classification, reconciliation state, and operation kind. Do not represent a system category as a fake category ID. Existing imported values that fall outside new-entry choices remain renderable through explicit legacy/current-value options.

At the end of Milestone 3, the operation interface must support an immutable client operation ID, operation kind, origin, and SCD2 leg relationships to logical transaction IDs. At the end of Milestone 6, reconciliation must expose account-local draft, apply, history, and working-set endpoints plus a persisted commit identifier and state.

Revision note (2026-08-21): Initial plan created after product-owner manual validation and adversarial review of funding, cutover, transfer, provenance, and reconciliation behavior. It records the decision to make reconciliation—not transfer pairing—the financial correctness gate.

Revision note (2026-08-21): Expanded recovery, command-idempotency ordering, per-leg rich-operation inputs, transfer-boundary rules, reconciliation schemas and digests, milestone-specific verification, and path-scoped commit safety after independent plan review.

Revision note (2026-08-21): Implemented Milestone 6 with a minimal four-table evidence schema, pure comparison/digest code, idempotent apply, backend classification contract, reopening-by-query, investment-status preservation, and balance-first account-detail UI; source-record decision UI remains explicitly deferred rather than partially implemented.
