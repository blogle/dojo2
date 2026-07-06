# ExecPlan: Assets & Liabilities Domain Model

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

The Assets & Liabilities page needs a backend model that can represent budget accounts, legacy tracking accounts, investment accounts, loans, and tangible assets without guessing from UI labels or metadata. After this work, dojo can import Aspire budget accounts and net-worth snapshot accounts safely, keep all financial entities rooted in the existing account identity model, and derive budget effects from explicit account/category links without mutating transaction rows. The first implementation pass deliberately stops before the frontend page is completed; it proves the backend foundation with fixture import, budget formula, net-worth, SCD2, and property tests.

This repository is pre-alpha for local data compatibility. The implementation may update the current DuckDB schema directly and require developers to recreate/reimport local databases. Do not build compatibility migrations unless a later decision changes this constraint.

## Progress

- [x] (2026-07-06) Interviewed product owner on account classes, links, loans, investments, tracking polarity, reconciliation, and first milestone scope.
- [x] (2026-07-06) Captured agreed backend-first scope in this ExecPlan.
- [ ] Implement first milestone: clean schema/domain foundation, Aspire import mapping, generic account-budget links, derived activity engine, tests, and user-facing one-page docs.
- [ ] Implement later milestones for investment positions/cash/prices, loan details/snapshots/attributions, reconciliation evidence, normalized read APIs, and frontend page integration.

## Surprises & Discoveries

- Existing `budget_account_settings.linked_payment_category_id` is credit-card-specific but already encodes the first account-linked budget behavior. It should be migrated into a generic account-budget link model instead of copied into new special cases.
- Existing Aspire net-worth import already reads `NetWorthDebts` and flips debt amounts negative. That gives a source for explicit tracking account polarity when the sheet provides it.
- The existing Assets & Liabilities Vue files are present but not routed and are not a trustworthy implementation target until backend entity semantics are modeled.

## Decision Log

- Decision: Keep every financial entity rooted in `accounts` with explicit account class values.
  Rationale: This preserves account identity, SCD2 account history, transaction references, and net-worth references while avoiding separate root identity systems.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Use explicit account classes, including `BUDGET`, `TRACKING`, `INVESTMENT`, `LOAN`, and `TANGIBLE_ASSET`.
  Rationale: Richer entity behavior differs materially. Explicit classes avoid dispatching on metadata and make service logic easier to test.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Aspire budget accounts import as `BUDGET`; Aspire net-worth categories import as dumb `TRACKING` accounts with explicit asset/liability polarity.
  Rationale: The importer must preserve Aspire history and not infer richer investment, loan, or tangible-asset behavior from legacy spreadsheet categories.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: If Aspire tracking polarity is not explicit, infer it from the latest non-zero snapshot amount and flag it during onboarding for correction.
  Rationale: Import should proceed for legacy sheets while still surfacing an important classification choice to the user.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Replace credit-card-specific linked category storage with generic `account_budget_links`.
  Rationale: Credit-card payment categories, investment contribution categories, and loan planning links are all account/category relationships, but only some create derived budget activity.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Account-budget links are one category to many accounts per behavior; an account may have at most one active category for a given behavior.
  Rationale: Many accounts can share an Investments category, but one account cannot safely dispatch one contribution transfer to two categories for the same behavior.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Derived budget activity is computed on read, not persisted.
  Rationale: Existing credit-card behavior is derived today. Persisted derived rows would introduce stale-state risk before benchmarks prove a need.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Links have a financial `effective_date` distinct from SCD2 `valid_from`.
  Rationale: `valid_from` records when configuration changed in dojo; `effective_date` controls which financial activity the link applies to.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Loan category links are planning/context links only in the first pass.
  Rationale: Plain mortgage-category transactions do not identify which loan changed when one category links to multiple loans. Loan balances change through balance snapshots/reconciliation, not category spend.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Loan payment attribution is SCD2 editable domain data linking one transaction to one loan; it does not store reconciliation IDs or principal/interest splits.
  Rationale: Reconciliation is a separate verification commit. Principal versus non-principal cost is derived from attributed transaction totals and principal balance snapshots.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Investment value comes from SCD2 positions, SCD2 cash snapshots, and separate price snapshots.
  Rationale: Holdings and cash are reconciled against brokerage statements, while separate price snapshots allow later market-data updates without bloating position history.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Brokerage statement prices outrank market-data prices on reconciliation dates.
  Rationale: Statement prices are authoritative evidence for exact account-value reconciliation. Market data is useful for current estimates but must not override statement evidence.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Reconciliation commits are generic lightweight evidence, not copies of domain records.
  Rationale: SCD2 tables are the historical source of truth. A reconciliation run records the entity, effective date, verified time, source summary, and relevant logical IDs/version timestamps.
  Date/Author: 2026-07-06 / opencode and product owner

- Decision: Maintain one user-facing domain one-pager for now.
  Rationale: These rules are essential for users to operate the app correctly, but the docs should not be fragmented before the domain stabilizes.
  Date/Author: 2026-07-06 / opencode and product owner

## Outcomes & Retrospective

No implementation has started. This plan records the shared model and narrows the first task to a backend foundation that can be verified independently before frontend work continues.

## Context and Orientation

dojo currently has a FastAPI backend in `api/src/dojo/`, a DuckDB schema in `api/src/dojo/sql/schema/current.sql`, and a Vue frontend in `web/src/dojo/`. Editable domain rows use SCD2 history: current rows have `valid_to` equal to the repository `MAX_TS` constant. The service layer in `api/src/dojo/service.py` shapes account, budget, category, transaction, and net-worth reads from DuckDB.

The existing account model has `accounts.account_class` plus a budget-only `budget_account_settings` table with `budget_account_type`, `linked_payment_category_id`, and `display_liability_positive`. That shape is too narrow for Assets & Liabilities because it only models budget accounts and credit-card payment behavior. The existing importer creates budget accounts from Aspire account ranges and creates tracking accounts from Aspire net-worth categories that do not duplicate budget accounts.

The term "derived activity" means category activity computed from existing ledger rows and account/category links without adding a category ID to transfer rows and without creating persisted synthetic transaction rows. Credit-card payment category behavior is already derived this way in focused code; this work generalizes that concept.

The term "reconciliation commit" means a record that a user or source verified the relevant domain records for one entity as of a date. It is not a database transaction and it does not copy all domain rows.

## Plan of Work

First, update the backend schema in `api/src/dojo/sql/schema/current.sql` to use explicit account classes and add type-specific tables without preserving old local database compatibility. Keep `accounts` as the root table for every entity. Add `tracking_account_details` or equivalent for tracking polarity. Add `account_budget_links` with SCD2 fields, `account_id`, `category_id`, `link_behavior`, and `effective_date`. Add empty type-specific tables needed by later milestones: loan details and balance snapshots, loan payment attributions, investment positions, investment cash snapshots, investment price snapshots, tangible asset valuation snapshots, and generic reconciliation runs/evidence. Do not wire every table into the UI yet.

Second, update importer parsing and persistence so Aspire budget accounts remain `BUDGET`, and every non-duplicate Aspire net-worth category becomes a `TRACKING` account with explicit asset/liability polarity. Use Aspire asset/debt ranges when present. If polarity metadata is absent, infer from the latest non-zero imported amount and emit an onboarding/import validation warning. Do not infer `INVESTMENT`, `LOAN`, or `TANGIBLE_ASSET` from Aspire names or amounts.

Third, migrate credit-card linked payment categories into the new `account_budget_links` concept in the freshly provisioned schema and service write paths. Preserve `budget_account_type` for budget-account subtypes such as deposit and credit card. Remove the budget-only `linked_payment_category_id` decision from formulas after replacement, but keep behavior identical for current fixture data.

Fourth, extract a shared derived category activity function in backend domain/service code. It should handle `CREDIT_CARD_PAYMENT` and `INVESTMENT_CONTRIBUTION` explicitly. `LOAN_PAYMENT` links remain planning/context links and must not create automatic budget activity. The function must take plain rows or typed domain-shaped records and return derived category effects deterministically. Keep database access outside the pure function.

Fifth, add tests before and after the refactor. Existing fixture import, budget formulas, net-worth totals, and credit-card payment category behavior must not regress. Add property tests for investment contribution transfers once investment accounts and links exist: a transfer from a budget account to a linked investment account is net-worth neutral, does not create reportable income or economic spending, and reduces the linked contribution category available amount. Add tests that loan-linked category transactions do not change loan balances.

Sixth, update docs and product spec. `SPEC.md` should capture the clarified durable behavior: all Aspire net-worth entities import as tracking accounts, loan links are planning links until explicit attribution/reconciliation, investment values use positions/cash/prices, and reconciliation commits are lightweight evidence. `docs/src/assets-and-liabilities-domain.md` should be the single user-facing one-pager for now.

Seventh, only after the backend foundation is validated, add or update API read models. Prefer one normalized `GET /api/assets-liabilities` overview read model so the frontend does not compose accounts, tracking snapshots, investment positions, cash, prices, loan snapshots, and reconciliation state itself. Detail endpoints can be type-specific later.

Eighth, defer frontend page completion until the backend read model exists. Existing files under `web/src/dojo/pages/AssetsLiabilitiesPage.vue`, `AccountDetailPage.vue`, and `web/src/dojo/components/accounts/` may be reused, but they must not drive backend design.

## Concrete Steps

Run commands from the repository root `/home/ogle/src/dojo2`.

Milestone 1 is the first implementation task. Edit `api/src/dojo/sql/schema/current.sql`, `api/src/dojo/api/models.py`, `api/src/dojo/service.py`, `api/src/dojo/importer.py`, and focused SQL files under `api/src/dojo/sql/queries/` as needed. Add or update backend tests under `api/tests/`, especially `test_migrations.py`, `test_importer.py`, `test_api_endpoints.py`, `test_budget_formulas.py`, and `test_properties.py`.

After Milestone 1, run:

    just migration-check
    just test-unit
    just test-integration
    just test-property
    just architecture-check

If frontend or docs are touched in the same implementation batch, also run:

    just docs
    just test-web

Before claiming the feature complete, run:

    just check

## Validation and Acceptance

Milestone 1 is accepted when a fresh database provisions successfully, importing `fixture://default` succeeds, existing budget and net-worth fixture assertions still pass, and new tests prove the following behavior:

- Aspire budget accounts import as `BUDGET` accounts.
- Aspire non-duplicate net-worth categories import as `TRACKING` accounts, not richer entities.
- Tracking accounts have explicit asset/liability polarity.
- Existing credit-card payment category values are unchanged after moving to generic account-budget links.
- Derived activity is computed on read and no persisted synthetic transaction rows are created.
- Loan-linked category transactions do not change loan balances.

Later milestones are accepted when investment account value can be computed as holdings plus cash using source-prioritized prices, loan non-principal cost can be derived from attributed transactions and principal balance snapshots, reconciliation commits can record lightweight evidence, and the frontend overview consumes the normalized backend read model.

## Idempotence and Recovery

This repository is pre-alpha for database compatibility. A developer can recover from schema changes by deleting the local DuckDB file and reimporting fixture or source data. Implementation steps should still be idempotent for fresh provisioning: running `just migration-check` repeatedly should produce the same valid schema.

Do not revert unrelated untracked or modified frontend files while implementing this plan. Stage only intended files for each commit.

## Artifacts and Notes

The first task should update these durable artifacts:

- `SPEC.md` for product behavior and acceptance criteria.
- `ARCHITECTURE.md` for runtime schema/domain model changes.
- `DECISIONS.md` if a durable tradeoff is not already captured in this ExecPlan and affects future implementation choices.
- `docs/src/assets-and-liabilities-domain.md` for user-facing operating rules.

The frontend mock screens in `plans/2026-06-17-implement-product-spec/assets_liabilities_screens/` remain visual references. If a mock conflicts with `SPEC.md`, `SPEC.md` wins.

## Interfaces and Dependencies

Account classes should be explicit constants or literal types in Python and TypeScript after implementation. Avoid raw string dispatch outside boundary parsing.

`account_budget_links.link_behavior` should support at least `CREDIT_CARD_PAYMENT`, `INVESTMENT_CONTRIBUTION`, and `LOAN_PAYMENT`. Only the first two create derived budget activity in the first implementation pass.

Investment price selection should prefer brokerage statement prices for reconciliation-date views and market-data prices for current estimate views when no statement price applies.

Loan attribution should relate one transaction to one loan account. Do not support one transaction split across multiple loans in the first model.

Reconciliation evidence should refer to logical IDs and SCD2 version timestamps rather than duplicating full records.
