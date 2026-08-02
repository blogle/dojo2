# Product Spec

## Current Product Behavior

dojo currently provides:

* onboarding that can import a deterministic repository fixture or a Google Sheet through the backend OAuth flow
* a DuckDB-backed financial ledger with SCD2 history for editable financial and configuration records
* a budget view with Available to Budget, grouped categories, starting available, month activity, and month budgeted values
* bounded transaction listing with server-side pagination and frontend bounded state
* account listing with actual, pending, cleared, and display balances
* transaction creation, editing, status changes, deletion, and account transfers
* category-group, category, and account management
* net-worth reporting that combines ledger-derived budget-account balances with imported tracking valuations while avoiding double-counting duplicate budget-account valuations

## Product Direction

dojo is a native personal-finance application heavily informed by the Aspire budgeting spreadsheet, but implemented as a purpose-built application for performance, correctness, extensibility, and better long-term support for net worth, investment tracking, reconciliation, and historical state.

The product centers on a versioned financial ledger. Rather than mutating important financial records in place, dojo preserves historical record versions using SCD2 semantics so that users can inspect changes over time, reconcile against external sources of truth, and eventually time travel through application state.

The application is designed primarily for high-density financial work rather than decorative dashboarding. It should make it fast to inspect accounts, budget categories, transactions, and obligations, while still surfacing warnings, funding pressure, and reconciliation needs.

## Product Principles

* spreadsheet-inspired where useful, but not constrained by spreadsheet interaction limits
* fast, dense, and keyboard-friendly for frequent financial workflows
* user-facing terminology should remain financial and plain-language rather than technical
* editing, removal, and reconciliation should preserve historical truth rather than destroying prior state
* simple and common actions should be directly accessible; advanced and diagnostic workflows may live behind secondary surfaces
* the application normally shows current state, but its data model must support future historical inspection and reconciliation review

## Canonical Terminology

The following terms are canonical throughout the application:

| Intent                                               | Canonical term       |
| ---------------------------------------------------- | -------------------- |
| Begin adding a record or entity                      | Add                  |
| Abandon an operation                                 | Cancel               |
| Persist form changes                                 | Save                 |
| Budget envelope                                      | Category             |
| Parent container                                     | Category group       |
| Desired funding state                                | Goal                 |
| Derived monthly requirement                          | Monthly funding      |
| Assign money to a category                           | Fund                 |
| Reassign category money                              | Move funds           |
| Money not assigned to categories                     | Available to budget  |
| Soft-delete a category or group                      | Retire               |
| Return a retired item to active use                  | Restore              |
| Correct an existing record                           | Edit                 |
| Remove an active transaction while retaining history | Remove               |
| Validate against an external source                  | Reconcile            |
| Persist a reviewed reconciliation                    | Apply reconciliation |

The implementation may internally use SCD2 revisions, diffs, commits, validity ranges, or similar concepts. Normal application language should remain financial and user-facing. Technical terminology may appear only in advanced or diagnostic views.

## Application Shell

dojo uses a compact, expandable left navigation rail. The rail must consume as little permanent screen space as practical so that tables, charts, and financial data can use the full viewport.

### Navigation Behavior

The collapsed rail displays icons for:

* Dashboard
* Budget
* Transactions
* Assets & Liabilities

Each icon has a tooltip and a clear selected state.

The rail can expand to reveal destination labels. Expansion and collapse use a subtle width and label-opacity animation. The user can keep the rail expanded or collapsed, and the preference persists between sessions.

The navigation must not automatically expand on hover. Expansion should require deliberate user action.

The application utility area may contain:

* current or historical as-of date
* items requiring attention
* application settings
* user menu

The default application state is always the current date. Historical state becomes available through future time-travel functionality.

## Onboarding

### Purpose

dojo includes a simple first-run onboarding flow for users who do not yet have application data.

The onboarding flow answers one question:

* Start with an empty application
* Migrate existing records from a Google Aspire sheet

This is intentionally lightweight. It is not yet a guided setup wizard.

### When Onboarding Appears

The onboarding screen is shown when:

* the user opens dojo for the first time
* no application data has been created or imported yet

Once the user has entered the application with data present, onboarding is no longer shown as the default entry screen.

### Layout

Onboarding is a pre-application screen and does not use the full in-app navigation shell.

The screen contains:

* product title
* brief explanation of the two starting paths
* two primary actions:

  * **Start empty**
  * **Migrate from Aspire**

The layout should be simple, centered, and low-friction.

### Path 1: Start Empty

Selecting **Start empty** immediately enters the application with no data populated.

The user lands in the normal application shell and may manually begin adding:

* category groups
* categories
* accounts
* transactions
* other supported records

No additional setup steps are required in this path.

### Path 2: Migrate from Aspire

Selecting **Migrate from Aspire** advances the user to a simple import form.

#### Aspire Migration Form

The form contains:

* a text field for the Google Sheet ID
* a **Submit** button
* a **Cancel** action returning to the initial onboarding choice screen

The screen clearly indicates that dojo will request read access to the specified Google Sheet in order to import data.

The input expects the Google Sheet ID.

### OAuth Consent

After the user submits a sheet ID, dojo begins the Google authorization flow.

The user is shown the Google OAuth consent screen requesting read access to the specified sheet.

If the user grants permission, dojo proceeds to migration.

If the user denies permission or the flow fails, the user returns to the migration form with a clear error message and may retry or cancel.

### Migration Progress Screen

Once permission is granted, dojo displays a dedicated progress screen while it reads, analyzes, prepares, commits, or validates Aspire data.

This screen contains:

* a migration-in-progress indicator
* high-level progress messaging
* a statement that the application is importing and validating records

This is a blocking state. The user is not taken into the application until required review steps are complete and migration either succeeds or fails.

### Net-Worth Duplicate Review

Aspire migration includes a required review step after dojo reads and analyzes the Aspire sheet and before migration is committed.

Purpose:

```text
Confirm which Aspire net-worth snapshot categories duplicate budget accounts so dojo does not double count them in the first net-worth total.
```

The review screen shows:

* budget accounts found
* net-worth categories found
* suggested duplicates
* items needing review
* items that will import as tracking accounts
* each net-worth category’s latest snapshot value
* suggested treatment
* matched budget account when applicable
* confidence level
* action to change the treatment

Each net-worth category must resolve to one treatment:

* Duplicate of budget account
* Import as tracking account
* Do not import

dojo suggests matches using best-effort heuristics such as normalized names, account metadata when available, latest snapshot value, ledger-derived budget-account balance, polarity, and account type.

High-confidence duplicate matches may be preselected. Low-confidence likely duplicates are marked **Needs review** and require explicit user confirmation before migration can continue.

This review is not a general migration editor. The user must not be asked to edit imported transactions, categories, historical values, or allocations during onboarding.

Aspire net-worth snapshot categories that duplicate budget accounts are excluded from active net worth so dojo does not double count ledger-derived budget-account balances.

### Migration Completion Screen

When migration completes successfully, the user sees a completion screen with:

* a success message
* a **Details** button
* a **Continue to app** button

#### Continue to App

Selecting **Continue to app** enters the normal application shell with imported data loaded.

#### Details

Selecting **Details** opens a modal showing:

* imported record counts
* validation-check summary
* non-blocking warnings
* validation warnings
* duplicate snapshot categories excluded from active net worth
* tracking accounts created
* net-worth categories not imported
* enough detail for auditability

The modal is informational and dismissible. Closing it returns the user to the migration completion screen, where they can continue to the application.

A drawer may be used only if the validation summary later proves too dense for the modal. The intended default is modal.

### Failure States

The onboarding flow must handle:

* invalid or missing Google Sheet ID
* Google authorization denied
* Google authorization failure
* read failure
* import failure
* validation failure severe enough to prevent import

On failure, the user remains in onboarding and is shown:

* a concise explanation of the problem
* the relevant next action, such as retrying, correcting the sheet ID, or cancelling

### Onboarding Terminology

Use the following labels consistently:

* **Start empty**
* **Migrate from Aspire**
* **Submit**
* **Cancel**
* **Details**
* **Continue to app**

Do not mix these with alternatives such as “Create new,” “Import workbook,” “Get started,” or “Finish.”

### Out of Scope for Current Onboarding

The following are explicitly not part of the current onboarding flow:

* multi-step guided setup
* manual configuration walkthroughs
* importing from sources other than Aspire
* editing imported data during onboarding
* advanced migration conflict resolution beyond the required net-worth duplicate review
* accepting anything other than the Google Sheet ID as migration input

## Core Screens

dojo currently centers on four primary destinations:

* Dashboard
* Budget
* Transactions
* Assets & Liabilities

Additional detail pages and modals are subordinate surfaces rather than primary navigation destinations.

## Goal Types

dojo supports three category goal types.

### One-Time Goal

A finite amount required by a specific date.

Examples include a wedding, vacation, or one-off purchase.

Configuration fields:

* goal amount
* goal date
* derived monthly funding

Changing the goal date immediately re-derives the monthly funding needed from the current application date or selected historical context.

### Recurring Goal

A mandatory expense that repeats on a known schedule and whose omission has an operational or contractual consequence.

Examples include a mortgage, insurance premium, utility bill, or subscription.

Configuration fields:

* amount per occurrence
* frequency
* next due date
* derived monthly funding

The recurrence schedule is defined by the combination of frequency and next due date.

### Discretionary Goal

This goal represents optional or lifestyle spending that may remain unfunded without causing loss of service, default, eviction, or another direct obligation.

Examples include travel, dining out, hobby purchases, or personal spending.

Configuration fields:

* monthly goal
* no due date

In the Budget table, its Due date cell displays **No due date** rather than an empty value.

## Dashboard

### Purpose

The Dashboard is a fixed-layout financial health summary. It lets the user quickly determine:

* whether their financial resources are outpacing their spending
* whether their net financial position is improving or deteriorating
* whether investments are supporting or eroding their position
* which categories contribute most heavily to spending
* which categories are consistently exceeding their goals
* which discretionary categories could be reduced
* which bills or obligations need attention
* whether a watched category has enough available money for a contemplated purchase
* whether accounts or valuations need reconciliation

The Dashboard is not a fully configurable widget canvas. It uses stable sections whose contents can be configured.

### Fixed Sections

#### Financial Trajectory

This is the dominant Dashboard section.

It displays:

* current net worth
* net-worth change over the selected period
* investment change over the selected period
* income over the selected period
* activity over the selected period
* net financial change
* cash-flow result

The principal summary should communicate whether resources exceeded spending in plain language.

Transfers between owned accounts do not count as either income or spending.

Investment performance and cash flow remain separately visible so that market gains do not disguise unsustainable recurring spending.

The trend chart supports:

* configurable period
* hover or drag inspection
* delta measurement between two points
* navigation to the relevant Assets & Liabilities detail

#### Spending Pressure

This section identifies where spending deserves attention.

It may show:

* highest-activity categories
* categories exceeding their monthly goals
* categories repeatedly exceeding goals across recent periods
* largest increases compared with the prior comparable period
* discretionary categories most suitable for reduction

Each item links to the category detail modal.

#### Upcoming Obligations

This section shows recurring and one-time goals that are due soon or underfunded.

Each item includes:

* category
* due date
* amount due
* available amount
* shortfall
* direct Fund action

Simple funding interactions may occur directly from the Dashboard. More involved investigation opens the Budget page or category detail modal.

#### Category Watchlist

The user chooses categories they frequently inspect.

Each watched category shows:

* category name
* available amount
* monthly goal or next obligation
* current funding state
* any overspending or underfunding warning

#### Asset and Liability Watchlist

The user chooses entities they want to monitor.

Each item may show:

* name
* current value or balance
* period change
* compact trend
* reconciliation freshness

#### Reconciliation Attention

Once reconciliation is implemented, the Dashboard flags:

* accounts not reconciled within the expected interval
* external values awaiting review
* unapplied reconciliation changes
* conflicting records that require resolution

Selecting the warning navigates to the relevant account or entity detail page. Reconciliation is not performed directly on the Dashboard.

### Income, Spending, and Budget Activity

The Dashboard should distinguish income, economic spending, budget activity, and net-worth movement.

Budget activity is how budgeted cash is assigned, consumed, released, or moved through categories. Economic spending is actual consumption or cost that reduces net worth, such as purchases, interest, fees, and losses.

Investment contributions are budget activity, but they are not economic spending. Investment withdrawals are not income. Loan principal payments are budget activity and cash-flow obligations, but the principal portion is net-worth neutral. Loan interest and fees are economic spending.

The Dashboard should avoid treating investment contributions or investment withdrawals as income or spending, while the Budget page should still show category activity for contribution planning.

### Dashboard Configuration

Users may:

* select categories in the category watchlist
* select entities in the asset and liability watchlist
* reorder entries within each watchlist

The overall section layout remains fixed.

## Budget

### Page Summary

The Budget header displays:

* current date or selected as-of date
* Available to budget
* activity
* budgeted

“Spent this month” is not displayed separately because it duplicates Activity.

Primary actions are:

* Add category
* Add category group

### Historical Context

The application normally shows current state.

Future historical support consists of two independent concepts:

* a budget period or month governing monthly activity
* an application-wide as-of date governing which SCD2 record versions are visible

Historical mode must be visibly indicated.

### Category Hierarchy

The table is ordered as follows:

1. Credit Card Payments
2. user-defined category groups and their categories
3. Uncategorized

Empty category groups are valid and may remain indefinitely.

Uncategorized is available as the parent selection when adding or editing a category.

### Reordering Mode

The normal table does not expose drag controls.

The user enables a dedicated reordering mode before hierarchy changes become available.

While reordering mode is enabled, the user can:

* reorder user-defined category groups
* move a category higher or lower within its group
* drag a category into another group
* drag a category into Uncategorized

Moving a group moves all of its children.

Changes remain visibly pending until the user selects Save or Cancel.

### Table Columns

The desktop table uses explicit columns:

| Category | Goal | Due date | Available | Activity | Budgeted |
| -------- | ---: | -------- | --------: | -------: | -------: |

For a discretionary goal:

* Goal displays the monthly goal amount
* Due date displays “No due date”

### Row States

Row states are additive rather than mutually exclusive.

A row may simultaneously be:

* underfunded
* due soon
* overspent
* uncategorized
* system-provided
* retired

Each state has an independent semantic representation.

### Category and Group Detail

Selecting a category or group opens a full-screen trouser (right-side overlay panel). The trouser covers the full viewport height and most of the width, leaving the navigation rail visible.

The trouser includes:

* name and group name
* action buttons at the top (Fund, Move funds, Edit configuration) — plain buttons without surface containers
* tabs: Overview, Funding history, Spending history

#### Overview Tab

The overview tab displays:

* summary metrics: current available, monthly goal, budgeted this month, activity this month
* goal configuration (goal type, monthly goal, start month, target amount, target date, rollover, incremental)
* goal progress with visual indicator
* funding to date: expected funding, actual funding, deviation from plan, additional monthly funding needed, spending reduction needed

#### Funding History Tab

Funding history shows a filtered view of the category allocations table, scoped to the selected category.

#### Spending History Tab

Spending history shows a filtered view of the transactions table, scoped to the selected category.

Group values are aggregates of their active child categories.

### Funding Shortcuts

Funding a category is initiated by selecting the Fund button in the category detail trouser. This opens a dedicated funding modal.

The funding modal presents:

* funding options: Fund up to next month, Fund to monthly goal, Custom amount
* every option displays the exact amount that will be funded
* a preview section showing: amount being funded, resulting category balance, resulting Available to budget
* a warning when Available to budget will become negative after the action

Before Save, the modal previews the action results. Funding a category succeeds even when Available to budget becomes negative. The application then displays a persistent warning until the deficit is corrected.

### Move Funds

1. Open a category detail trouser
2. Select Move funds
3. Choose a source or destination category
4. Enter an amount
5. Review resulting balances
6. Select Save

The interaction creates the necessary underlying allocation records.

### Fund Category Group

Group funding is partial rather than atomic.

Processing order:

1. categories with an actual due date before categories without one
2. earlier due dates before later due dates
3. recurring goals before one-time goals when otherwise tied
4. discretionary goals last
5. categories higher in the current table order as the final tie-breaker

Overspending does not move a category ahead of one with an earlier due date.

The operation proceeds category by category:

1. fully fund each category when sufficient money remains
2. when the remaining Available to budget is insufficient for the next category, partially fund that category
3. stop when no Available to budget remains
4. display a summary of fully funded, partially funded, and unfunded categories

This flow never makes Available to budget negative.

### Allocation Records

Allocation records are available from an Advanced section in the category or group detail trouser. The Funding history tab provides a filtered view of allocations scoped to the selected category.

### Retired Categories

Use the terms:

* Retire
* Retired categories
* Restore

A secondary Budget-page action opens a large retired-items modal.

### Budget Activity vs Economic Spending

Budget activity and economic spending are different concepts.

Budget activity records how money inside the budget is planned, assigned, consumed, released, or moved through categories. Economic spending records actual consumption or cost that reduces net worth.

Investment contributions consume linked contribution-category funds for budget planning, but they are not economic spending. Loan payments record the full cash obligation against the payment category, but only interest, fees, losses, and other non-principal costs are economic spending.

## Transactions

### Page Summary

The page displays the selected month with:

* inflow
* outflow
* net

### Entry Form

The form uses:

* date
* account
* category
* amount
* direction selector
* memo

The direction selector defaults to **Outflow**.

After a successful entry:

* date retains its previous value
* account retains its previous value
* category resets
* amount resets
* memo resets
* focus moves to the field most useful for the next entry

Enter submits a valid transaction.

### Canonical Input Order

Every transaction receives an immutable logical entry position.

Display order is configurable:

* oldest entry first
* newest entry first

Changing display direction does not mutate the underlying logical order and does not sort transactions by transaction date.

### Ledger Behavior

The ledger supports:

* virtualized infinite scroll
* account filtering
* exact date filtering
* date-range filtering
* category filtering
* exact or ranged amount filtering
* reconciliation-state filtering
* display of active records by default

### Edit Flow

1. Select a row
2. The row enters inline edit state
3. Edit fields in place
4. Changes commit when the row loses focus (blur)
5. Press Escape to cancel the draft before commit
6. The previous version becomes inactive
7. A replacement version becomes active
8. The logical transaction remains in the same entry position
9. Status is toggled via an inline pill (Pending / Cleared)

### Remove and Undo

1. Select a row
2. Select the delete action at the right edge of the active row
3. The current record becomes inactive
4. A toast appears at the bottom right:

   * Transaction removed
   * Undo

Selecting Undo restores the transaction through the versioned record model.

### Unreconciled Working Set

Transactions changed since the last successful reconciliation form the account’s current working set.

This includes:

* added transactions
* edited transactions
* removed transactions
* restored transactions

The Transactions page exposes a filter or indicator for **Changes since last reconciliation**.

### Account Scope

The Transactions page shows transaction-ledger activity for budget accounts and account transfers. Tracking accounts and tangible assets are outside the normal Transactions page unless a future feature explicitly adds a specialized flow for them.

Investment account transfers remain two-leg account transfers on the transaction ledger. Tracking-account cutovers are not ledger transfers.

## Account and Entity Semantics

### Purpose

dojo distinguishes budget accounts from other assets and liabilities so the application can preserve Aspire history, avoid double counting net worth, and support richer account types over time.

Budget accounts are inside the budget boundary. Tracking accounts, investment accounts, loans, and tangible assets are outside the budget boundary unless a future feature explicitly states otherwise.

Net-worth neutral does not always mean budget neutral.

### Budget Accounts

A budget account is an account inside the budget boundary.

A budget account:

* participates in the Transactions page
* participates in budget category activity
* contributes to Available to budget through existing budget mechanics
* has a balance derived from transaction ledger entries
* contributes to net worth from its ledger-derived actual balance
* must not also contribute imported net-worth snapshot values
* may be a deposit account or credit-card-style budget account

Imported Aspire net-worth snapshots matching a budget account are not active net-worth entities. They may be retained as migration evidence, but they do not contribute to active net worth.

Credit card budget accounts remain a special budget-account case with linked payment categories. This is an account-category linkage used for budget behavior and does not change the existing credit-card conceptual model.

### Account-Linked Budget Behavior

Some accounts define a linked budget category and a link behavior. This allows the budget engine to interpret ordinary ledger activity without changing the transaction row shape.

The transaction ledger remains account-centric. A transfer is still represented as two transaction rows with `system_category = TX_ACCOUNT_TRANSFER`. The transaction rows are not assigned a budget category.

The linked behavior determines whether those transfer rows create derived budget effects.

Credit-card payment categories, investment contribution categories, and loan payment categories are all examples of account-linked budget behavior. A link is effective from a financial effective date. That effective date is distinct from SCD2 configuration history: configuration history records when dojo learned about the link, while the effective date controls which financial activity the link applies to.

Links are one category to many accounts for a behavior. One account must not have two active categories for the same behavior at the same time. This keeps derived budget behavior unambiguous while allowing several brokerage accounts to share one Investments category.

Examples:

```text
Visa credit card
  linked category: Visa Payment
  behavior: CREDIT_CARD_PAYMENT

Brokerage investment account
  linked category: Investment Contributions
  behavior: INVESTMENT_CONTRIBUTION

Mortgage loan
  linked category: Mortgage
  behavior: LOAN_PAYMENT
```

Transfers remain the source of account-balance truth. Linked account-category behavior determines how certain transfers affect budget categories.

Derived budget effects are computed on read from ledger rows and account-budget links. dojo must not persist synthetic transaction rows merely to represent derived category activity unless future benchmarks prove a cache or derived table is required.

### Tracking Accounts

A tracking account is a legacy or manual snapshot-authoritative entity outside the budget boundary.

A tracking account:

* does not participate in the Transactions page
* does not participate in budget categories
* does not use ledger transactions as its source of truth
* contributes to net worth from the latest snapshot at or before the selected as-of date
* is the direct migration target for non-budget Aspire net-worth categories
* exists primarily for Aspire compatibility and manually updated assets or liabilities

Tracking accounts should remain simple. They should not be treated as transfer endpoints in normal budgeting workflows.

Tracking accounts carry explicit asset/liability polarity. Aspire imports derive this from Aspire net-worth asset and debt metadata when available. If the source does not identify polarity, dojo infers it from the latest non-zero snapshot amount and flags the choice during onboarding so the user can correct it.

Tracking snapshot entry uses unsigned user-facing amounts. The account's polarity determines whether the value contributes to net worth as an asset or liability. A new snapshot for a date that already has a snapshot corrects that date through the versioned record model rather than creating two competing effective values. Tracking snapshots cannot use a future effective date.

For a tracking account, recording a snapshot is the complete current value-update workflow. Until generic reconciliation is implemented, the UI shows snapshot source, date, and freshness rather than a separate reconciliation state or action.

### Investment Accounts

An investment account is a richer non-budget asset entity outside the budget boundary.

An investment account:

* can receive investment contribution transfers
* can send investment withdrawal or capital-return transfers
* may have valuations, performance changes, holdings, or richer investment detail in the future
* is not a budget account
* does not make transfers count as income or economic spending
* contributes to net worth from its current value, valuation, or activity according to the richer investment model
* carries self-managed flag and tax treatment metadata for portfolio and withdrawal planning

Investment account value is derived from versioned holdings plus versioned cash. A holding records a ticker, quantity, and average basis. Prices are recorded separately from holdings so brokerage statement prices and future market-data prices can coexist without rewriting position history. Brokerage statement prices are authoritative for reconciliation-date values; market-data prices may be used for current estimate views when they do not override statement evidence.

Investment accounts are reconciled through dated statement snapshots of holdings, prices, and cash. dojo does not require a separate trade, dividend, interest, or sale-proceeds entry workflow. A user who records statement snapshots after each brokerage event can obtain event-level resolution; a user who reconciles less often sees statement-to-statement portfolio changes.

Between statement snapshots, cleared investment contributions and withdrawals adjust the last reconciled cash value provisionally. Only transfers after the inclusive statement-snapshot date are applied, so a later statement snapshot supersedes those provisional deltas without double counting them. Pending transfers remain visible but do not change actual investment value or net worth. The UI identifies post-snapshot value as provisional until the next investment reconciliation.

Moving cash from checking to brokerage is net-worth neutral. It is not income and it is not economic spending. It does affect budget planning because money has left the set of budget accounts available for spending.

dojo handles this through ordinary account-transfer rows plus linked account-category behavior. The transaction ledger remains account-centric, and the budget engine derives category effects from account configuration and transfer direction.

#### Linked Investment Contribution Category

An investment account may have a linked contribution category. This category is used to plan and reserve budget funds before investment contributions are made.

The link is prospective:

* Linking an existing category must never reinterpret historical category activity.
* Linking an existing category must never create, mutate, or backfill ledger rows.
* Linking an existing category must never initialize or change the investment account from prior category transactions.
* Future transfer rows touching the linked investment account use the linked behavior for derived budget reporting.
* Historical Aspire or pre-link transactions in a category such as `Stonks` remain unchanged.

Linking a category to an investment account never causes historical category activity to create investment account activity.

Linked investment categories do not create, mutate, or backfill ledger rows.

The linked category affects budget reporting prospectively through derived budget behavior on future transfer rows.

When creating or configuring an investment account, the UX should offer:

* Create a new contribution category, such as `Investment Contributions`
* Link an existing category from today or a chosen effective date forward
* Do not link a category yet

The UI must clearly state that past activity in a linked existing category remains unchanged.

#### Investment Contribution Transfers

A transfer from a budget account to an investment account remains a two-leg account transfer on the transaction ledger.

The canonical ledger representation is:

```text
Checking account   -$1,000   TX_ACCOUNT_TRANSFER
Brokerage account  +$1,000   TX_ACCOUNT_TRANSFER
```

If the destination investment account has linked behavior `INVESTMENT_CONTRIBUTION`, dojo derives budget activity for the linked category from the transfer amount. This reduces the linked category’s available amount, just as spending from a category would, but it does not count as economic spending or reportable income.

The derived behavior represents:

* budget-account cash outflow
* investment-account value or cash increase
* derived budget activity against the linked contribution category
* net-worth-neutral balance-sheet movement
* no reportable income
* no economic spending

Example:

```text
Checking account:                 -$1,000, TX_ACCOUNT_TRANSFER
Brokerage account:                +$1,000, TX_ACCOUNT_TRANSFER
Investment Contributions activity: -$1,000
Net worth change:                  $0
Reportable income:                 $0
Economic spending:                 $0
```

The user mental model is:

```text
I budgeted $1,000 for investing.
I transferred $600 to brokerage.
I have $400 left available in Investment Contributions.
```

The linked contribution category should feel like a normal budget category from the user perspective, but the activity is derived from transfer rows touching the linked investment account rather than from `category_id` on the transfer transaction.

The contribution category can be funded in advance through normal allocation from Available to budget. If the category is not sufficiently funded, the transfer flow should require the user to choose how to handle the shortfall. The default is to fund the linked contribution category from Available to budget, then perform the contribution. If that makes Available to budget negative, dojo uses the existing negative-ATB warning behavior.

The contribution flow previews the two transaction legs, the linked-category activity, resulting category availability, resulting Available to budget, and net-worth-neutral reporting effect before Save.

The transaction row is not augmented to carry both `category_id` and `system_category`.

#### Investment Withdrawals

A transfer from an investment account to a budget account remains a two-leg account transfer on the transaction ledger.

Canonical ledger representation:

```text
Brokerage account  -$1,000   TX_ACCOUNT_TRANSFER
Checking account   +$1,000   TX_ACCOUNT_TRANSFER
```

Default semantics:

* investment account decreases
* budget account increases
* net worth is unchanged
* not reportable income
* not economic spending
* returned cash increases Available to budget by default
* a future UX may optionally route returned cash directly to a category

Example:

```text
Brokerage account:  -$1,000, TX_ACCOUNT_TRANSFER
Checking account:   +$1,000, TX_ACCOUNT_TRANSFER
Available to budget +$1,000
Net worth change:   $0
Reportable income:  $0
Economic spending:  $0
```

By default, the returned cash increases Available to budget. It is not income and does not represent investment performance. Future UX may allow routing returned cash directly to a category. Investment gains and losses are represented separately through valuation or performance records, not as income caused by withdrawals.

### Loans

A loan is a richer liability entity outside the budget boundary.

A loan:

* tracks an outstanding obligation
* may have an opening balance
* may have principal, interest, fees, escrow, manual adjustments, and reconciliation history
* contributes to net worth as a liability
* may have a default payment category
* does not replace the related budget category

A loan stores loan details such as original loan amount, origination date, and rate when known. Its current principal balance comes from reconciled or manually entered principal-balance snapshots. The related budget category plans the cash obligation; it does not by itself determine loan principal movement.

A user may have both a `Mortgage` budget category and a `Mortgage` tracking account or richer loan entity.

The category answers: “How much cash do we need to budget for this obligation?”

The loan answers: “What is the outstanding balance-sheet liability?”

Creating a richer loan entity does not require retiring the related budget category.

#### Loan Payment Operations

Future loan payments should be modeled as loan payment operations, not as simple account transfers.

A loan payment operation links:

* a budget-account cash outflow
* a budget category, usually the loan’s default payment category
* optional loan balance effects

A loan payment may contain:

* principal amount
* interest amount
* fee amount
* escrow amount
* split state: `unknown`, `estimated`, or `reconciled`

Required semantics:

* The budget category records the full cash obligation.
* Principal reduction is net-worth neutral because cash decreases and liability decreases.
* Interest and fees reduce net worth.
* If the split is unknown when the payment is entered, dojo records the budget transaction and category activity first and marks the loan payment split as unknown.
* The split may be completed later through edit or reconciliation.
* Historical Aspire mortgage payments must not be backfilled into principal and interest components.

Historical Aspire transactions are not backfilled into principal and interest components.

Example:

```text
Checking account:        -$4,000
Mortgage category:       $4,000 activity
Mortgage loan principal: -$1,250 liability reduction
Interest / fees / escrow: $2,750 non-principal cost
```

The exact internal representation may evolve, but the product semantics must remain stable.

Until a dedicated loan-payment flow exists, dojo may let the user attribute an existing budget transaction to one loan. That attribution is editable domain data, not a reconciliation record. A single transaction is attributed to at most one loan. Principal versus non-principal cost is derived from attributed transaction totals and principal-balance snapshots. For example, if attributed mortgage transactions total $5,000 for a period and the principal balance decreases by $2,000, dojo can report $3,000 as non-principal cost for that period. dojo does not persist a finer interest, fee, or escrow split in the first model.

The first loan-payment model uses this lightweight attribution approach rather than requiring a split during transaction entry. Recording a payment from loan detail creates an ordinary budget transaction with the loan and its payment category preselected. On the Transactions page, a uniquely linked payment category attributes the transaction automatically. If several loans share the category, dojo asks for the loan in a follow-up control rather than adding a permanent loan column to the transaction table.

New attribution behavior is prospective. Historical transactions are not automatically backfilled or reinterpreted.

Loan reconciliation captures a statement period and the lender's current principal, accrued interest, escrow, and unapplied-credit balances. Given the previously verified principal, current principal, attributed payments in the period, and any explicit principal-changing adjustments, dojo derives the aggregate principal reduction and the remaining unallocated non-principal cash. dojo must label that remainder as unknown non-principal unless lender statement detail supplies a more precise classification; it must not guess that the remainder is interest, fees, or escrow.

Escrow and unapplied credit are separate balances rather than immediate economic spending. Escrow is shown as a restricted asset separately from the loan liability; it must not be silently netted into the loan's displayed net-worth contribution. Unapplied credit is also presented separately when supplied. A later reconciliation may optionally record lender-provided component detail, but ordinary payment entry and historical import never require per-payment principal, interest, fee, escrow, or unapplied allocation.

Loan creation requires current principal and its as-of date so a newly created loan immediately has a truthful obligation. Original loan amount, origination date, and rate remain optional historical and projection metadata.

Loan configuration supports an estimated amortization model with interest rate, fixed or variable rate type, scheduled principal-and-interest payment, payment frequency, next payment date, maturity date or remaining term, and optional recurring extra principal. Escrow is excluded from the scheduled principal-and-interest amount.

The amortization model projects interest, principal, remaining balance, payoff date, and extra-payment effects. Each statement reconciliation resets the projection to actual lender principal and regenerates the future schedule. Projected values are labeled **Estimated** and never presented as reconciled facts.

Loan reconciliation primarily asks for statement date, principal, and escrow. Accrued interest and unapplied credit are optional advanced fields. Optional lender-provided year-to-date principal paid and year-to-date interest paid provide actual cumulative reporting without per-payment backfill. The UI distinguishes lender-provided actual values, balance-derived values, estimated values, and unknown non-principal cash.

### Tangible Assets

A tangible asset is a non-budget asset entity outside the budget boundary.

A tangible asset:

* normally uses valuation snapshots or manual valuations
* contributes to net worth from its current valuation
* does not participate in the Transactions page by default
* does not create budget activity merely because its valuation changes
* may later support purchase or sale flows, but valuation changes are not income, spending, or budget activity

Tangible-asset valuation entry uses positive user-facing amounts. Same-date valuation entry corrects the existing dated value through SCD2 history. Future-dated valuations are rejected. The latest effective valuation is the tangible asset's source of truth for Assets & Liabilities and net worth.

Examples include a home, vehicle, jewelry, or collectibles.

### Budget Boundary

Budget accounts are inside the budget boundary. Tracking accounts, investment accounts, loans, and tangible assets are outside the budget boundary unless a future feature explicitly states otherwise.

Transfers and operations behave differently depending on whether they stay within or cross this boundary:

| Movement                                 | Net worth         | Income/spending    | Budget effect                                          |
| ---------------------------------------- | ----------------- | ------------------ | ------------------------------------------------------ |
| Budget account → budget account          | neutral           | no                 | budget-neutral account transfer                        |
| Budget account → investment account      | neutral           | no                 | investment contribution consumes linked category funds |
| Investment account → budget account      | neutral           | no                 | returns cash to Available to budget by default         |
| Budget account → loan                    | partially neutral | interest/fees cost | loan payment category records full cash obligation     |
| Tracking account → richer entity cutover | neutral           | no                 | no budget effect; representation change                |
| Tangible asset valuation change          | changes net worth | no                 | no budget effect                                       |

### Tracking Account Upgrade and Cutover

Users can progressively upgrade legacy tracking accounts to richer account types without rewriting history.

A tracking account is not converted in place into a richer account type.

The upgrade flow is:

1. User creates a new richer entity, such as an investment account, loan, or tangible asset.
2. dojo proposes an opening value or opening balance from the latest tracking-account snapshot at or before the cutover date.
3. User confirms the cutover date and opening value or balance.
4. dojo retires the old tracking account effective the same cutover date.
5. dojo links the new entity to the retired tracking account as its replacement.
6. Historical as-of views before the cutover use the tracking account.
7. Current and future views after the cutover use the richer entity.

One tracking account may be replaced by more than one richer entity. For example, one Aspire brokerage tracking category may be allocated across several real investment accounts. All successor entities in one cutover share the cutover date and receive their own opening statement snapshot or valuation.

Before applying cutover, dojo compares the latest tracking value at the cutover date with the combined opening values of all successors. The user reviews the variance and confirms a final tracking reconciliation that records a final source snapshot equal to the successor total. This preserves the prior imported snapshot history and prevents the representation change itself from creating income, spending, budget activity, or a net-worth jump.

The cutover date is inclusive for successors: historical views before the date use the tracking account; views on and after the date use the successor entities. A completed cutover is one atomic operation that records the final tracking reconciliation, creates all successors and opening values, records replacement links, and retires the predecessor from current totals. Repeating or partially applying the operation must not duplicate entities or values.

The cutover opening value is not a transfer, income, spending, or budget activity. It is a representation change.

The cutover must not be described as moving the balance through the ledger. For non-budget tracking-to-rich-entity upgrades, use **opening balance** or **opening value**, not **account transfer**.

### Aspire Migration Rules

Aspire data has both budget-ledger records and separate net-worth snapshot categories. dojo imports both concepts while avoiding double counting and without rewriting Aspire history.

Aspire migration behavior:

1. Import Aspire budget accounts as dojo budget accounts.
2. Import Aspire transaction history into the ledger.
3. Preserve existing Aspire account-transfer rows between budget accounts as budget-neutral account transfers.
4. Import Aspire category allocations as dojo allocations.
5. Analyze Aspire net-worth snapshot categories.
6. For each Aspire net-worth category, resolve one treatment: Duplicate of budget account, Import as tracking account, or Do not import.
7. Budget-account duplicates do not create active tracking accounts and do not contribute snapshot values to active net worth.
8. Non-budget net-worth categories become tracking accounts with imported snapshot history and explicit asset/liability polarity.
9. The importer must not infer investment accounts, loans, tangible assets, linked investment contribution behavior, loan principal/non-principal splits, or other rich account behavior from Aspire net-worth categories or ordinary historical category transactions.
10. The importer must preserve historical Aspire behavior rather than rewriting it.

Historical category activity like `Stonks` or `Mortgage` must not be automatically reclassified into linked investment behavior or rich loan behavior during migration.

Users can later create richer investment, loan, or tangible-asset entities and cut over from legacy tracking accounts. That cutover is a representation change, not a ledger transfer.

## Assets & Liabilities

### Page Purpose

The page remains named **Assets & Liabilities**.

### Structure

The overview page groups entities into:

* cash and equivalents
* investments
* tangible assets
* credit
* loans

Entities are displayed as stacked, full-width row cards rather than a tile grid.

### Stacked Entity Cards

A card may show:

* name
* entity type
* institution
* partial account number
* APY or type-specific metadata
* current balance or valuation
* pending amount
* period change
* source of truth
* reconciliation freshness
* attention state

The source of truth describes how the current value is determined. Examples include ledger, snapshot, investment activity or valuation, loan balance, and manual valuation.

Every displayed value and date is derived from the entity's real source of truth. The page must not display fabricated period change, fallback dates, attention state, or reconciliation freshness. Until reconciliation evidence exists, the truthful state is **Not reconciled**, not **Up to date**.

Period change compares the current effective value with the latest effective value at or before the start of the selected period. When no earlier value exists, the UI displays an unavailable state rather than zero. Attention state may identify stale or missing source values, pending provisional investment value, or missing reconciliation evidence; it must not default every entity to **OK**.

### Add Entity

The page provides one primary action:

* Add item

The wizard first selects the entity type.

Supported names are:

* budget account
* tracking account
* investment account
* loan
* tangible asset

Institution entry uses one consistent free-text combobox across entity creation, configuration, and cutover. It suggests common institutions and institutions already present in dojo while accepting any custom value.

Investment creation configures its prospective linked contribution category. Loan creation configures its prospective linked payment category. Contribution and payment operations display the configured category and its available balance rather than asking the user to select the relationship on every operation.

### Detail Pages

Selecting a stacked card opens a dedicated detail page.

All detail pages display:

* name
* type
* metadata
* reconciliation state and freshness
* record history
* edit configuration

#### Budget Account Detail

Budget account details include:

* ledger-derived balance
* transaction ledger filtered to that account
* reconciliation status
* account metadata
* record history
* edit configuration

#### Tracking Account Detail

Tracking account details include:

* latest snapshot value
* snapshot history
* add or edit snapshot
* replacement or cutover affordance
* retired or replaced state when applicable

Adding a snapshot supports both a new effective date and correction of an existing date. The detail page always uses the latest effective snapshot, not a transaction-ledger balance.

#### Investment Account Detail

Investment account details include:

* current value
* self-managed flag
* tax treatment
* contribution category link
* contribution and withdrawal activity
* valuation or performance history
* contribution flow
* withdrawal flow
* reconciliation status

The investment activity list contains contribution and withdrawal transfers plus statement reconciliation events. Trades, dividends, interest, and sale proceeds are represented through changes between holdings, cash, and price snapshots rather than separate manual transaction-entry workflows.

The current value is the latest reconciled holdings-plus-cash value plus cleared contribution and withdrawal cash deltas after that reconciliation. The page distinguishes reconciled and provisional portions.

Investment statements may contain cash and no holdings. A cash-only investment account is valid.

When a cleared contribution occurs after reconciliation on the same calendar date, it is provisional and changes current value. Statement and transaction recording timestamps disambiguate same-day ordering. A later statement correction supersedes only transfers included by that correction.

Derived contribution activity appears in the linked category's monthly Activity and spending history without adding `category_id` to either transfer leg. Investment withdrawals never affect the linked contribution category and return cash to Available to budget.

#### Loan Detail

Loan details include:

* current obligation
* default payment category
* payment activity
* principal, interest, fees, and escrow split state
* reconciliation status
* payment flow
* edit configuration

Payment entry does not require the user to allocate principal, interest, fees, escrow, or unapplied amounts. The detail page shows attributed payments, the latest statement balances, aggregate principal reduction, and unknown non-principal remainder until reconciliation supplies more detail.

#### Tangible Asset Detail

Tangible asset details include:

* current valuation
* valuation history
* metadata
* reconciliation or manual update status

Tangible-asset detail uses valuation history and a valuation trend. It does not show the ordinary transaction ledger unless a future purchase or sale feature explicitly introduces such activity.

### Transaction Settlement and Balances

Pending and Settled are transaction settlement states:

* Pending: posted but not cleared
* Settled: cleared

Actual represents the current true balance or obligation presented at the account level.

## Reconciliation

### Purpose

Reconciliation validates dojo’s current working records against an external source of truth.

Reconciliation may validate:

* budget-account ledger records against bank or source records
* tracking-account snapshots against external statement values
* investment-account value or activity against brokerage statements
* loan balances and payment splits against lender statements
* tangible-asset valuations against manual or external valuation sources

For loan payments, reconciliation may complete or correct unknown principal, interest, fee, or escrow splits.

For tracking-account upgrades, reconciliation must not backfill pre-cutover rich-account history.

### Entry Point

Complex reconciliation begins from the relevant asset or liability detail page.

The Dashboard may report that reconciliation is overdue or incomplete, but it only navigates to the relevant detail page.

### Working-Set Model

Each account or entity has:

* a last applied reconciliation
* a current working set of changes made since that reconciliation
* an external source value or record set
* a proposed reconciled state

The working set depends on the account or entity type. Budget accounts use ledger records. Tracking accounts use snapshot values. Investment accounts use account-transfer rows plus value and activity records. Loans use obligation balances, payment records, and split state. Tangible assets use valuation records.

Reconciliation commits are lightweight evidence that relevant records for one entity were verified as of a date. They record the entity, effective date, verification time, source summary, and references to relevant logical records and SCD2 version timestamps. They do not copy full domain records; the SCD2 tables remain the historical source of truth.

The user reviews the difference between:

1. the last reconciled state
2. the current dojo working state
3. the upstream source of truth
4. the proposed resulting state

### Proposed Flow

1. Open an account or entity detail page
2. Select Reconcile
3. Choose or provide the source-of-truth data
4. Review current balance or valuation differences
5. Review added, edited, removed, and unmatched records
6. Edit or amend dojo records as needed
7. Resolve conflicts
8. Review the resulting balance or valuation
9. Select Apply reconciliation
10. Save the reviewed state as the new reconciliation baseline

### User-Facing Language

Use:

* Changes since last reconciliation
* Source records
* Current records
* Proposed changes
* Conflict
* Include
* Exclude
* Apply reconciliation
* Reconciliation history
* Restore prior version

### Reconciliation Review Component

For each changed or conflicting record, display:

* previous reconciled value
* current dojo value
* source value
* proposed value
* difference
* reason or match status
* included or excluded state

The final review displays:

* source ending balance or valuation
* proposed dojo ending balance or valuation
* remaining difference
* number of records being added, changed, removed, or restored

## Time Travel

dojo supports both contextual history and future global historical state.

### Contextual History

Available from an individual:

* transaction
* category
* allocation
* account
* asset
* liability
* reconciliation

This view shows the item’s versions and changes over time.

### Global As-Of Mode

A future global control allows the user to view the application as it existed at a selected date or reconciliation point.

Global historical mode must:

* be visibly distinct from current mode
* display the selected as-of date persistently
* apply consistently across Dashboard, Budget, Transactions, and Assets & Liabilities
* preserve the canonical transaction entry order as it existed at that time
* avoid presenting current values as historical values

Historical state is read-only by default.

## Reusable Interaction Components

The application should implement the following shared components:

* compact expandable navigation rail
* page header
* metric strip
* attention panel
* period selector
* trend chart with interval measurement
* sparkline
* hierarchical category table
* virtualized transaction ledger
* filter bar
* stacked entity card
* large detail modal
* form modal
* entity wizard
* goal editor
* funding dropdown
* move-funds editor
* additive state indicators
* persistent warning banner
* confirmation dialog
* undo toast
* version-history view
* diff view
* reconciliation review
* historical-mode banner
* retired-items modal

## Acceptance Criteria

* `GET /health` and `GET /api/health` return a healthy application payload.
* `GET /api/app/status` and `GET /api/bootstrap` report readiness without returning a full data dump.
* A fresh repository environment can be set up with `just setup`.
* The API can be started with `just api`, which provisions the DuckDB schema explicitly before starting FastAPI.
* The web app can be started with `just web` and can reach the API through the configured base URL.
* `GET /api/transactions` accepts `offset`, `limit`, `sort_by`, and `sort_dir`, rejects unsupported sort fields, and returns bounded pages with `total` and `has_more` metadata.
* Automated checks exist for repository policy enforcement, fresh database provisioning, SCD2 history behavior, bounded transaction reads, and deterministic fixture-backed financial invariants.
* `just check` runs the normal local quality gate, and `just ci` runs the canonical CI command.

## Current Non-Goals

* production deployment workflows
* background job orchestration
* multi-user authentication and authorization
* browser e2e coverage through a full Cypress suite; the command surface reserves `just test-e2e`, but deterministic Cypress infrastructure is not yet implemented

## Known Gaps and Deferred Detail

The following areas are intentionally directionally specified but not yet fully modeled in this document:

* exact Dashboard formulas for net financial change and cash-flow result
* detailed validation-summary schema shown in the onboarding Details modal
* exact reconciliation source-ingestion mechanisms and provider-specific flows
* group-level move-funds distribution semantics when moving money at an aggregate level
* detailed investment holdings views, performance analysis, and aggregated position tracking
* Monte Carlo, forecasting, and future dedicated net-worth planning screens
* editing behavior, if any, while in future global historical mode
* full browser e2e coverage and deterministic Cypress infrastructure
