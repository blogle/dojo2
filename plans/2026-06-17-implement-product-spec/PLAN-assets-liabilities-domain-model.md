# ExecPlan: Assets & Liabilities Domain Model

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

The Assets & Liabilities page needs a backend model that can represent budget accounts, legacy tracking accounts, investment accounts, loans, and tangible assets without guessing from UI labels or metadata. After this work, dojo can import Aspire budget accounts and net-worth snapshot accounts safely, keep all financial entities rooted in the existing account identity model, and derive budget effects from explicit account/category links without mutating transaction rows. The first implementation pass deliberately stops before the frontend page is completed; it proves the backend foundation with fixture import, budget formula, net-worth, SCD2, and property tests.

This repository is pre-alpha for local data compatibility. The implementation may update the current DuckDB schema directly and require developers to recreate/reimport local databases. Do not build compatibility migrations unless a later decision changes this constraint.

## Progress

- [x] (2026-07-06) Interviewed product owner on account classes, links, loans, investments, tracking polarity, reconciliation, and first milestone scope.
- [x] (2026-07-06) Captured agreed backend-first scope in this ExecPlan.
- [x] (2026-07-07) Aligned on unified derived activity model: all three account types (credit card, investment, loan) use transfer-in to linked account as the derived activity trigger. Forward-only derivation. No retroactive interpretation of legacy data.
- [x] (2026-07-07) Credit card link migration confirmed in scope: migrate `budget_account_settings.linked_payment_category_id` to `account_budget_links` now, not deferred.
- [x] (2026-07-07) Investment model infrastructure confirmed in scope: positions, cash snapshots, and price snapshot tables plus basic CRUD.
- [ ] Phase 1: Credit card link migration to unified `account_budget_links` model, import hygiene, domain table clearing.
- [ ] Phase 2: Investment model infrastructure (positions, cash, prices schema and CRUD).
- [ ] Phase 3: Snapshot and valuation CRUD APIs (tracking, loan, tangible).
- [ ] Phase 4: Fix derived activity engine and liability math.
- [ ] Phase 5: Read model enrichment (group totals, source-of-truth, as-of date).
- [ ] Phase 6: Account detail read completeness (join investment/loan details).
- [ ] Phase 7: Account update completeness and validation.
- [ ] Phase 8: Cleanup and full verification.
- [ ] (2026-07-31) Completion pass: connect rich records to one type-aware as-of value model, then implement tracking/tangible/investment/loan/cutover vertical slices. See `docs/plans/complete-assets-liabilities.md`.

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

- Decision: Unify derived activity model across credit card, investment, and loan account types.
  Rationale: All three use the same conceptual model: a transfer touches a linked account, and a budget category absorbs the transfer-in amount. This gives users one mental model rather than three separate patterns. Credit card payments, investment contributions, and loan payments all follow the same derivation rule: transfer-in to linked account on or after effective date reduces linked category available.
  Date/Author: 2026-07-07 / opencode and product owner

- Decision: Add `derivation_method` column to `account_budget_links` to distinguish credit card payment derivation (which sums spending plus transfer-in) from investment/loan derivation (which sums transfer-in only).
  Rationale: Credit card payment categories account for categorized spending on the card account in addition to transfers. Investment and loan categories only account for transfer-in amounts. Both reduce the linked category, but the credit card formula includes an additional term. A `derivation_method` field makes this explicit in the schema rather than relying on behavioral name matching.
  Date/Author: 2026-07-07 / opencode and product owner

- Decision: All derivation is forward-only from the link effective date.
  Rationale: Legacy Aspire data must not be retroactively reinterpreted. Transfers before the link effective date are untouched regardless of account type. This was previously agreed and is confirmed for the unified model.
  Date/Author: 2026-07-07 / opencode and product owner

- Decision: Transfer guardrails per account class are deferred to a later pass.
  Rationale: While valid, transfer guardrails require additional backend machinery that is not needed for the MVP. The existing SPEC wording captures intended semantics. Guardrails can be added after core functionality is working.
  Date/Author: 2026-07-07 / opencode and product owner

- Decision: Detail routes per account class are deferred to frontend screen builds.
  Rationale: The enriched `/api/accounts` response covers frontend needs for now. Dedicated per-class detail endpoints will be added when the corresponding frontend screens are built.
  Date/Author: 2026-07-07 / opencode and product owner

- Decision: Investment model infrastructure (positions, cash, prices tables) is included in this pass.
  Rationale: The backend machinery needs to be ready so frontend work can progressively expose investment account data. Basic CRUD endpoints for positions, cash snapshots, and prices are included. Full valuation calculation (positions + cash + prices → account value) is deferred to when frontend screens need it.
  Date/Author: 2026-07-07 / opencode and product owner

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

The first implementation pass has started. Schema tables for `tracking_account_details`, `investment_account_details`, `loan_details`, `loan_balance_snapshots`, `tangible_asset_valuations`, and `account_budget_links` have been added. Property tests for credit card, investment, and loan link behaviors have been added. The `/api/assets-liabilities` endpoint exists with basic grouping. However, the credit card link migration is incomplete (still using `budget_account_settings.linked_payment_category_id`), the derived activity engine has incorrect loan behavior, liability math is wrong for credit cards, and snapshot/valuation CRUD APIs are missing.

By 2026-07-31, most originally listed schema and append/list API scaffolding exists, but the outcome above is stale. The remaining blocker is a fragmented read model: investment positions/cash/prices, loan snapshots, and tangible valuations are not consistently used by accounts, Assets & Liabilities, or net worth. Append endpoints also need account-class validation, effective-date handling, and same-date correction semantics. The completion pass is therefore organized around observable vertical slices rather than checking off the obsolete scaffold phases.

## Context and Orientation

dojo currently has a FastAPI backend in `api/src/dojo/`, a DuckDB schema in `api/src/dojo/sql/schema/current.sql`, and a Vue frontend in `web/src/dojo/`. Editable domain rows use SCD2 history: current rows have `valid_to` equal to the repository `MAX_TS` constant. The service layer in `api/src/dojo/service.py` shapes account, budget, category, transaction, and net-worth reads from DuckDB.

The existing account model has `accounts.account_class` plus a budget-only `budget_account_settings` table with `budget_account_type`, `linked_payment_category_id`, and `display_liability_positive`. That shape is too narrow for Assets & Liabilities because it only models budget accounts and credit-card payment behavior. The existing importer creates budget accounts from Aspire account ranges and creates tracking accounts from Aspire net-worth categories that do not duplicate budget accounts.

The term "derived activity" means category activity computed from existing ledger rows and account/category links without adding a category ID to transfer rows and without creating persisted synthetic transaction rows. Credit-card payment category behavior is already derived this way in focused code; this work generalizes that concept.

The term "reconciliation commit" means a record that a user or source verified the relevant domain records for one entity as of a date. It is not a database transaction and it does not copy all domain rows.

## Plan of Work

The implementation proceeds in eight phases, building from schema correctness through API completeness. Each phase is independently verifiable.

Phase 1 migrates credit card payment links from `budget_account_settings.linked_payment_category_id` to the generic `account_budget_links` table. This unifies all three account-budget link types (credit card, investment, loan) in a single table. A `derivation_method` column distinguishes credit card derivation (spending plus transfer-in) from investment/loan derivation (transfer-in only). The import flow and `create_account()` are updated to write `account_budget_links` rows for credit cards. `list_categories()` is refactored to derive all linked behavior from the unified table. The legacy `linked_payment_category_id` column is removed.

Phase 2 adds investment model infrastructure: `investment_positions`, `investment_cash_snapshots`, and `investment_price_snapshots` schema tables with SCD2 history, `current_*` views, basic CRUD service methods, and route endpoints. Full valuation calculation is deferred.

Phase 3 adds snapshot and valuation CRUD APIs for tracking accounts, loans, and tangible assets using the payload models already defined.

Phase 4 fixes the derived activity engine to treat `LOAN_PAYMENT` links identically to `INVESTMENT_CONTRIBUTION` (transfer-in only). It also fixes `/api/assets-liabilities` liability math to use `actual_balance_minor` for credit cards.

Phase 5 enriches the `/api/assets-liabilities` response with per-group totals and per-item source-of-truth indicators.

Phase 6 completes account detail reads by joining investment and loan detail tables in `list_accounts.sql`.

Phase 7 completes account updates to persist detail-table changes and adds typed validation for account-class-specific fields.

Phase 8 cleans up stale references and runs full verification.

## Concrete Steps

Run commands from the repository root `/home/ogle/src/dojo2`.

Phase 1 is the first implementation task. Edit `api/src/dojo/sql/schema/current.sql` (add `derivation_method` to `account_budget_links`, remove `linked_payment_category_id` from `budget_account_settings`), `api/src/dojo/service.py` (refactor `list_categories()` to use unified link model, update `create_account()` for credit cards), `api/src/dojo/importer.py` (write `account_budget_links` rows for credit cards), and `api/src/dojo/sql/queries/list_accounts.sql` (remove legacy join). Add or update backend tests under `api/tests/`.

After each phase, run the narrowest relevant verification:

    just lint-api
    just test-unit
    just test-property
    just test-integration

After Phase 1, also run:

    just migration-check
    just architecture-check

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

`account_budget_links` is the single table for all account-category link relationships. It supports `link_behavior` values `CREDIT_CARD_PAYMENT`, `INVESTMENT_CONTRIBUTION`, and `LOAN_PAYMENT`. A `derivation_method` column distinguishes how derived activity is computed: `CC_SPEND_AND_TRANSFER` (credit card), `TRANSFER_IN_ONLY` (investment, loan), `NONE` (context-only placeholder).

All three link behaviors derive budget activity going forward from the link's `effective_date`. No retroactive interpretation of legacy data occurs.

Investment price selection should prefer brokerage statement prices for reconciliation-date views and market-data prices for current estimate views when no statement price applies.

Loan attribution should relate one transaction to one loan account. Do not support one transaction split across multiple loans in the first model.

Reconciliation evidence should refer to logical IDs and SCD2 version timestamps rather than duplicating full records.
