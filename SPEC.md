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

Once permission is granted, dojo displays a dedicated progress screen while migration runs.

This screen contains:

* a migration-in-progress indicator
* high-level progress messaging
* a statement that the application is importing and validating records

This is a blocking state. The user is not taken into the application until migration either succeeds or fails.

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
* advanced migration conflict resolution during onboarding
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

### Category and Group Detail Modal

Selecting a category or group opens a large modal.

The modal includes:

* name
* current available amount
* goal configuration
* historical activity
* historical funding
* goal progress
* expected funding to date
* actual funding to date
* deviation from the planned funding path
* additional monthly funding needed to recover
* spending reduction needed to recover
* funding actions
* move funds
* edit configuration
* advanced allocation records

Group values are aggregates of their active child categories.

### Funding Shortcuts

Funding shortcuts may be presented in a dropdown button.

Every option displays the exact amount that will be funded.

Before Save, the modal previews:

* amount being funded
* resulting category balance
* resulting Available to budget

Funding a category succeeds even when Available to budget becomes negative. The application then displays a persistent warning until the deficit is corrected.

### Move Funds

1. Open a category detail modal
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

Allocation records are available from an Advanced section or tab in the category or group detail modal.

### Retired Categories

Use the terms:

* Retire
* Retired categories
* Restore

A secondary Budget-page action opens a large retired-items modal.

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
2. The row enters edit state
3. Edit fields in place
4. Select Save or press Enter
5. The previous version becomes inactive
6. A replacement version becomes active
7. The logical transaction remains in the same entry position

Cancel exits editing without creating a new version.

### Remove and Undo

1. Select a row
2. Select Remove
3. Confirm removal
4. The current record becomes inactive
5. A toast appears at the bottom right:

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

## Assets & Liabilities

### Page Purpose

The page remains named **Assets & Liabilities**.

### Structure

Assets may be grouped into:

* cash and equivalents
* investments
* tangible assets

Liabilities may be grouped into:

* credit
* loans

### Stacked Entity Cards

Entities are displayed as stacked, full-width row cards rather than a tile grid.

A card may show:

* name
* entity type
* institution
* partial account number
* APY or type-specific metadata
* current balance or valuation
* pending amount
* period change
* reconciliation freshness
* attention state

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

### Detail Pages

Selecting a stacked card opens a dedicated detail page.

All detail pages display:

* name
* type
* metadata
* current balance or valuation
* reconciliation state and freshness
* historical values
* record history
* edit configuration

Budget account details include a filtered transaction ledger.

Tracking account details include snapshot history.

### Transaction Settlement and Balances

Pending and Settled are transaction settlement states:

* Pending: posted but not cleared
* Settled: cleared

Actual represents the current true balance or obligation presented at the account level.

## Reconciliation

### Purpose

Reconciliation validates dojo’s current working records against an external source of truth.

### Entry Point

Complex reconciliation begins from the relevant asset or liability detail page.

The Dashboard may report that reconciliation is overdue or incomplete, but it only navigates to the relevant detail page.

### Working-Set Model

Each account or entity has:

* a last applied reconciliation
* a current working set of changes made since that reconciliation
* an external source value or record set
* a proposed reconciled state

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

