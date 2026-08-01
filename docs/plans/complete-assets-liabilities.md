# Complete Assets & Liabilities with truthful type-specific values

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept current as implementation proceeds.

## Purpose / Big Picture

After this work, Assets & Liabilities will be a complete financial workflow rather than a visually aligned shell. Users can see values that agree across the overview, detail pages, and net worth; record and correct snapshots; reconcile investment holdings and loan statement balances; make investment contributions and withdrawals; attribute loan payments without entering statement splits; and replace one imported tracking account with one or more richer entities without changing net worth.

The observable result is that mocks 01 through 07 are represented by working screens, except that the generic reconciliation-review mock remains deferred. No screen invents a period change, date, attention state, note, or “Up to date” status.

## Progress

- [x] (2026-07-31) Audited current screens, API, persistence, tests, SPEC.md, and mocks 01–07.
- [x] (2026-07-31) Resolved product decisions for value signs, effective dates, investments, loan attribution, escrow, and one-to-many cutover.
- [ ] Milestone 1: implement one type-aware as-of value resolver and truthful overview/detail data.
- [ ] Milestone 2: complete tracking snapshot correction and tangible valuation flows.
- [ ] Milestone 3: complete investment statement reconciliation and holdings-plus-cash valuation.
- [ ] Milestone 4: complete investment contribution and withdrawal operations.
- [ ] Milestone 5: complete loan payment attribution and aggregate statement reconciliation.
- [ ] Milestone 6: complete one-to-many tracking cutover.
- [ ] Milestone 7: close mock-alignment gaps, remove inert controls, and run full verification.

## Surprises & Discoveries

- Observation: Rich records can be appended, but most do not participate in account lists, Assets & Liabilities totals, or net worth.
  Evidence: `api/src/dojo/service.py` reads `_latest_valuations_by_account()` for legacy values while investment positions, loan snapshots, and tangible valuations have separate append/list methods.

- Observation: Tracking detail displays the ledger-derived `display_balance_minor` even though snapshots are its source of truth.
  Evidence: `web/src/dojo/pages/AccountDetailPage.vue` uses `display_balance_minor` in tracking metrics while its history fetches nonzero tracking snapshots.

- Observation: Existing investment and loan transfer property tests use budget accounts as both endpoints, so they do not prove rich-account net-worth neutrality.
  Evidence: `api/tests/test_properties.py` investment and loan transfer scenarios do not create investment or loan account classes.

## Decision Log

- Decision: User-entered asset and obligation values are positive; entity type or polarity determines net-worth sign.
  Rationale: Forms should ask for the amount shown on a statement rather than make users encode accounting signs.
  Date/Author: 2026-07-31 / product owner and opencode

- Decision: Same-date snapshot entry corrects the existing logical dated value with SCD2 history; future values are allowed but excluded before effective.
  Rationale: Each entity needs one deterministic value per effective date while preserving correction history.
  Date/Author: 2026-07-31 / product owner and opencode

- Decision: Investment value is holdings plus cash, with statement prices preferred over estimates. Cleared transfers after the latest inclusive statement date adjust cash provisionally until superseded.
  Rationale: This preserves immediate net-worth neutrality without double counting transfers included by the next statement.
  Date/Author: 2026-07-31 / product owner and opencode

- Decision: Investment events are represented by statement snapshots at the user's chosen cadence, not a parallel trade/dividend/interest entry ledger.
  Rationale: Reconciliation after each event provides event-level detail without duplicate entry; less frequent reconciliation remains valid.
  Date/Author: 2026-07-31 / product owner and opencode

- Decision: Loan payment entry records or attributes an ordinary category transaction and leaves its split unknown. Reconciliation captures aggregate statement balances.
  Rationale: Users should not enter principal, interest, fees, escrow, and unapplied amounts for every payment. Ending principal can derive aggregate principal reduction; unavailable detail must remain explicitly unknown.
  Date/Author: 2026-07-31 / product owner and opencode

- Decision: One tracking predecessor can have several successors, and cutover performs a final source reconciliation to the successor total.
  Rationale: Imported Aspire categories can combine several real accounts. Matching the final predecessor value to successor openings makes cutover net-worth neutral and auditable.
  Date/Author: 2026-07-31 / product owner and opencode

## Outcomes & Retrospective

Implementation has not started. The requirements and dependency order are now explicit, and Dashboard work is blocked until this plan's acceptance behavior passes.

## Context and Orientation

The FastAPI/DuckDB backend lives in `api/src/dojo/`. `api/src/dojo/service.py` owns domain operations, `api/src/dojo/api/routes.py` parses HTTP requests, and SQL belongs in `api/src/dojo/sql/`. Editable records use SCD2: a correction closes the current row and inserts a new current version with the same logical identifier.

The Vue frontend lives in `web/src/dojo/`. `web/src/dojo/pages/AssetsLiabilitiesPage.vue` renders the overview, `AddItemWizardPage.vue` renders creation, and `AccountDetailPage.vue` currently branches across every account class. API calls are in `web/src/dojo/api/client.ts`. Mocks live in `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/`.

An effective date is the financial date on which a snapshot or configuration applies. It is distinct from the SCD2 validity timestamp, which records when dojo learned or changed the record. “As of” resolution first chooses records effective on or before the requested date and then chooses the SCD2 version known in the requested application state.

## Plan of Work

Milestone 1 introduces a typed account-value read model. It returns current value, signed net-worth contribution, source, effective date, reconciled/provisional state, and period change. Budget accounts resolve from the ledger; tracking and tangible entities from their latest effective valuation; investments from holdings plus cash and post-statement cleared transfer deltas; loans from statement balances. `list_accounts`, `get_assets_liabilities`, `get_net_worth`, detail metrics, summaries, and trends consume this model rather than reproducing class decisions.

Milestone 2 makes tracking and tangible records correctable. Append endpoints validate account class and foreign identity. Same-date writes replace the current version of the dated logical record. Tracking receives an Add snapshot form and tangible detail receives valuation history, trend, and Add valuation. Future records remain visible as scheduled history but do not affect current values.

Milestone 3 defines investment statement reconciliation as one atomic dated snapshot containing holdings, the prices used for those holdings, and cash. Positions gain a financial effective date. The detail page displays reconciled holdings, cash, statement-to-statement change, and provisional transfer deltas. Missing prices prevent a reconciled total rather than silently valuing a holding at zero.

Milestone 4 exposes account-budget links and creates identifiable paired transfer operations. Contribution previews the two ledger legs, linked-category activity, funding shortfall handling, resulting Available to budget, and zero net-worth/economic-spending effect. Withdrawal returns cash to Available to budget by default. A new statement snapshot inclusively supersedes earlier provisional deltas.

Milestone 5 adds prospective transaction-to-loan attribution. Loan detail payment entry preselects loan and category. Transaction-page entry infers a unique linked loan and asks only when several loans share the category. Statement reconciliation stores principal, accrued interest, escrow, and unapplied credit; derives aggregate principal reduction and unknown non-principal remainder; and never backfills historical splits.

Milestone 6 adds effective replacement relations and an atomic one-to-many cutover command. The flow collects successor types and opening statement values, compares their total with the predecessor, records a confirmed final predecessor snapshot equal to that total, creates all successors, and excludes the predecessor on and after the inclusive cutover date.

Milestone 7 aligns action hierarchy, title badges, tables, right rails, charts, and modal sizing with mocks 01–07 while respecting DESIGN.md and the intentionally collapsible navigation rail. It removes or disables every remaining inert control and updates current architecture, changelog, capability, baton, and validation documents.

## Concrete Steps

Run all commands from the repository root. Use the narrowest repository recipes after each milestone:

    just migration-check
    just architecture-check
    just test-unit
    just test-property
    just test-integration
    just lint-api
    just lint-web
    just typecheck
    just test-web

Run `just check` before declaring the plan complete. Record exact command results and visual screenshots in `plans/2026-06-17-implement-product-spec/VALIDATION.md`.

## Validation and Acceptance

For values, tests must prove that one tracking snapshot, tangible valuation, investment statement, or loan statement produces the same signed amount in account detail, Assets & Liabilities, and net worth. Future values do not apply early. Same-date corrections preserve SCD2 history and produce one effective result.

For investment transfers, a cleared contribution reduces a budget account and increases provisional investment cash by the same amount, consumes linked-category funds, reports no income or spending, and leaves net worth unchanged. A statement on the transfer date includes the transfer and supersedes it; a statement before it does not. Withdrawal is the inverse and returns budget cash to Available to budget.

For loans, payment entry never requires a split. Given previous principal of $200,000, current principal of $198,000, and $5,000 attributed payments with no other principal adjustment, reconciliation reports $2,000 principal reduction and $3,000 unknown non-principal. Escrow and unapplied credit remain separate balances.

For cutover, the day before uses only the predecessor. The cutover date and day after use all successors and not the predecessor. The final predecessor snapshot equals combined successor openings, no transaction or allocation is created, and net worth is unchanged across the boundary. One predecessor can create at least three successors in the acceptance scenario.

For UI alignment, Cypress exercises each supported action and modal. Visual review compares structure and hierarchy against mocks rather than using pixel diffs. No date, change, attention, note, or reconciliation state may be hardcoded as real data.

## Idempotence and Recovery

Schema provisioning remains safe on a fresh database. Compound operations use one DuckDB transaction. Snapshot correction keeps the same logical dated identity and can be retried after validation errors. Contribution, withdrawal, reconciliation, and cutover commands receive operation identities or enforce uniqueness so a client retry cannot duplicate money or successors.

If a milestone reveals a missing product decision, stop only that milestone, record the question in this plan, and continue no dependent work. Do not paper over unknown financial meaning with placeholder values.

## Artifacts and Notes

The baseline visual evidence is in `tmp/tracking-account-detail-desktop.png` and `tmp/tracking-cutover-modal.png`. These files are local review artifacts and are not part of the implementation commit.

## Interfaces and Dependencies

The value resolver must expose a typed result rather than an unstructured metadata dictionary. Its minimum fields are account identity/class, unsigned statement value when applicable, signed net-worth contribution, effective date, source kind, reconciliation state, provisional amount, and period change availability.

HTTP request models use Pydantic literals or enums for account classes, source kinds, and operation types. Vue uses discriminated unions for class-specific detail data and forms. Routers remain thin; financial arithmetic belongs in service/domain code and SQL resources. No new external dependency is required.

Revision note (2026-07-31): Initial plan created after the product-owner requirements session and repository/mock audit. It supersedes the stale claim that Assets & Liabilities Phase 6 was complete.
