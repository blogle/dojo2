# Engineering Product Specification: v0.1 Native Envelope Budgeting Application MVP

## 1. Introduction & Executive Summary

### 1.1 Product Goal

Build a native, local-first envelope budgeting web application that replaces an existing Aspire-style Google Sheets budget for daily household use.

The MVP must allow the household to migrate off the spreadsheet and begin dogfooding the native application immediately. The application must import historical operational budget data from a copied Google Sheet, reconstruct the current budget state, and support the core daily workflows:

1. View account balances.
2. View budget categories and category balances.
3. View Available to Budget.
4. Allocate money to categories.
5. Move money between categories.
6. Enter and edit transactions.
7. Track pending and cleared transactions.
8. Support Aspire-compatible credit-card budgeting behavior.
9. Preserve hidden categories and hidden accounts.
10. Import historical net worth snapshots without double-counting budget accounts.

The MVP must be usable locally from a developer laptop within one to two days of implementation work.

### 1.2 Source Spreadsheet Policy

The application imports from a Google Sheet copy only. The original production spreadsheet must never be modified or used as a writable source.

Expected source sheet title:

```text
Copy of Finances 2.0
```

The copied spreadsheet is a read-only bootstrap source. After import, the native DuckDB database becomes the source of truth.

### 1.3 Non-Goals for v0.1

The following are explicitly out of scope for MVP:

1. Kubernetes deployment.
2. Tailscale / Traefik configuration.
3. Public WAN exposure.
4. In-app backup/export UI.
5. Bank sync.
6. Plaid integration.
7. Receipt scanning.
8. Multi-currency support.
9. Full reconciliation workflow.
10. Brokerage position tracking.
11. Mortgage amortization.
12. Market price import.
13. Automated net worth mark-to-market.
14. Rich reporting dashboards.
15. Forecasting and planning scenarios.
16. Reimplementing unsupported custom spreadsheet tabs such as home scenarios or custom loan sheets.

Operational deployment, backups, and scheduled DB snapshots are handled outside the application for v0.1.

---

## 2. Product Principles

### 2.1 Correctness First

Financial correctness is more important than UI polish or performance micro-optimizations. The application must not migrate to native source-of-truth status unless it can reconstruct the operational state of the source budget.

### 2.2 Aspire-Compatible Behavior Without Spreadsheet Fragility

The application must reproduce the operational behavior of the imported spreadsheet while replacing spreadsheet formulas with explicit application models and tested SQL queries.

The app must not assume the reader or implementer understands Aspire Budgeting, YNAB, or envelope budgeting. All required behavior is defined in this spec.

### 2.3 Local-First, Single-Household Application

The MVP is intended for one household with low write concurrency. Writes are occasional human actions, not high-frequency financial ticks.

Expected write rate:

```text
approximately one write per minute during active use
```

### 2.4 Versioned State

The application is fully versioned using Slowly Changing Dimension Type 2 validity intervals.

SCD2 is mandatory across:

1. Transactions.
2. Allocations / budget movements.
3. Accounts.
4. Budget account settings.
5. Category groups.
6. Categories.
7. Budget buckets.
8. Net worth valuations.

Users can freely edit rows. They are not forced to provide reasons for edits. The app automatically preserves prior versions so history can be inspected and reverted.

### 2.5 No Magic NULL Semantics

A `NULL` value must never imply financial meaning.

Bad:

```text
category_id = NULL means Available to Budget
```

Good:

```text
system_category = TX_AVAILABLE_TO_BUDGET
bucket_type = BUCKET_AVAILABLE_TO_BUDGET
```

### 2.6 Domain Tables Stay Clean

Do not add row-level spreadsheet provenance columns to core domain tables.

Do not add:

```text
source_sheet
source_row_number
source_cell
imported_row_id
```

to transactions, allocations, categories, accounts, or valuations.

A minimal import summary table is allowed, but row-level provenance is intentionally omitted.

### 2.7 12-Factor Configuration

All environment-specific configuration must be supplied through environment variables.

No environment-specific URLs, OAuth redirect URIs, secrets, hostnames, or paths may be hardcoded.

The application must support local execution and future Kubernetes deployment by changing environment variables only.

---

## 3. MVP Scope

### 3.1 In Scope

The MVP must include:

1. Local web application.
2. Vue.js frontend.
3. FastAPI backend.
4. DuckDB canonical database.
5. Google OAuth user-consent onboarding.
6. Google Sheets read-only import by pasted sheet URL or ID.
7. Import of:

   * Configuration
   * Transactions
   * Category Allocation
   * Net Worth Reports
8. Import of visible and hidden categories.
9. Import of visible and hidden accounts.
10. Budget dashboard.
11. Transaction entry and editing.
12. Account balance display.
13. Pending/cleared status support.
14. Category/group/account editing.
15. Budget funding and move-money workflows.
16. Aspire-compatible credit-card budgeting semantics.
17. Month-to-month category rollover.
18. Net worth snapshot import.
19. Minimal imported net worth display or API readiness.
20. Unit, property, integration, component, and limited E2E tests.

### 3.2 Out of Scope but Roadmapped

The following must be documented as future work:

1. Reconciliation sessions.
2. Net worth dashboard.
3. Brokerage/retirement position tracking.
4. Market price imports, e.g. yfinance.
5. Mortgage/loan tracking.
6. Rich spending reports.
7. Backup automation.
8. Split DuckDB read/write paths.
9. Home infrastructure deployment.
10. User roles and multi-user access controls.

---

## 4. Technical Stack

### 4.1 Backend

```text
Python
FastAPI
DuckDB
Pydantic
pytest
Hypothesis
uv
```

### 4.2 Frontend

The frontend must use Vue.js.

Required:

```text
Vue 3
TypeScript
Vue Router
Pinia or simple Vue composables for state
Tailwind CSS
Vitest
Vue Test Utils
Cypress
```

Allowed virtualizers:

```text
TanStack Virtual
VueUse virtual list utilities
```

Do not use React.

Do not use:

```text
React
TanStack Router
TanStack Query
TanStack Table
```

The application should avoid the full TanStack suite for simple data grids. Use simplified Vue reactive state and focused virtualized list/table primitives for DOM culling.

### 4.3 Table and List Performance

Large lists must use virtualization.

Required virtualized surfaces:

1. Transactions table.
2. Account detail transaction list.
3. Import validation detail list.
4. Future reconciliation diff table.

The virtualizer must cull DOM nodes outside the viewport. The app must not render tens of thousands of rows directly.

### 4.4 Development Environment

Use:

```text
uv for Python dependency management
npm or pnpm for frontend dependencies
Nix flake for system dependencies
```

The Nix flake should provide system tools only, such as:

```text
python
uv
nodejs
npm/pnpm
duckdb CLI
just or make, optional
```

### 4.5 Database

DuckDB is the canonical database for MVP.

Rationale:

1. The application is local/single-household.
2. Write frequency is low.
3. The main workload is analytical rollup over historical ledgers.
4. DuckDB is well suited to aggregations, filters, and reporting.
5. Future reporting and net worth analytics are columnar workloads.

### 4.6 Database Concurrency

DuckDB read/write concurrency limitations are accepted for v0.1.

MVP uses:

```text
one backend process
one DuckDB connection
application-level write lock
```

Do not implement split read/write connections in v0.1.

Roadmap follow-up:

```text
evaluate dedicated DB worker or split read/write connections for concurrent reads
```

---

## 5. Configuration and Environment Variables

### 5.1 Required Environment Variables

The app must be configured entirely via environment variables.

Required backend variables:

```text
APP_ENV
APP_BASE_URL
API_BASE_URL
FRONTEND_BASE_URL
DUCKDB_PATH
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT_URI
GOOGLE_OAUTH_SCOPES
SESSION_SECRET
```

Optional variables:

```text
LOG_LEVEL
CORS_ALLOWED_ORIGINS
DEV_FIXTURE_MODE
```

### 5.2 OAuth Redirect URI

The Google OAuth redirect URI must be driven entirely by:

```text
GOOGLE_OAUTH_REDIRECT_URI
```

No redirect URI may be hardcoded in code.

Local example:

```text
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/onboarding/google/callback
```

Future Kubernetes example:

```text
GOOGLE_OAUTH_REDIRECT_URI=https://budget.example.internal/api/onboarding/google/callback
```

The same code must work in both environments.

### 5.3 12-Factor Rule

All environment differences must be handled through environment variables, not code branches.

Bad:

```python
if ENV == "local":
    redirect_uri = "http://localhost:8000/..."
else:
    redirect_uri = "https://..."
```

Good:

```python
redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
```

---

## 6. Visual Design System

### 6.1 Aesthetic Direction

The MVP UI must use a minimalist, modern brutalist design system.

The UI should feel:

```text
dense
sharp
calm
legible
financial
not generic SaaS
not bubbly
not animated-heavy
not dashboard-template-like
```

### 6.2 Color Palette

Use an earth-tone palette restricted to:

1. Dark browns.
2. Muted greens.
3. Off-whites.

Allowed palette tokens:

```text
bg-off-white        #F4F1EA
bg-warm-paper       #ECE5D8
bg-muted-sand       #D8CDBB

text-dark-brown     #241C15
text-soft-brown     #4A3728
text-muted-brown    #6B5848

border-brown        #8A7664
border-tan          #C8B8A6

green-muted         #3F6B4A
green-dark          #2E4D36
green-pale          #DCE8D8

brown-negative      #6F3F2A
brown-warning       #8A5A32
```

Do not use bright blues, purples, neon greens, gradients, glassmorphism, or generic Bootstrap-like palettes.

### 6.3 Layout Rules

1. Use square corners.
2. Prefer 1px borders.
3. Avoid shadows except for focus rings if necessary.
4. Avoid decorative animations.
5. Use high-density tables.
6. Use clear typographic hierarchy.
7. Use monospace numbers for financial amounts.
8. Use strong alignment for money columns.
9. Support keyboard-heavy entry.

### 6.4 Typography

Recommended:

```text
UI font: system sans-serif
numeric font: system monospace
```

Financial values must use tabular/monospace number styling.

### 6.5 Components Must Not Look Generic

Do not use off-the-shelf component defaults without restyling.

Buttons, tables, inputs, cards, and modals must follow the earth-tone brutalist design constraints.

---

## 7. Core Domain Concepts

### 7.1 Envelope Budgeting

Envelope budgeting means money is assigned to named budget categories before or as it is spent.

The household has:

1. Accounts containing real-world balances.
2. Categories representing spending or saving envelopes.
3. Category groups organizing categories.
4. A special system bucket called Available to Budget.
5. Transactions that change account balances and category activity.
6. Allocations that move money between budget buckets.

### 7.2 Account Classes

Use only:

```text
BUDGET
TRACKING_BALANCE
TRACKING_POSITIONS
TRACKING_DEBT
```

#### BUDGET

Budget accounts participate in daily envelope budgeting.

Examples:

```text
checking
savings
cash
credit cards
```

Credit cards are `BUDGET` accounts with special metadata and linked payment categories.

#### TRACKING_BALANCE

Manually valued net worth accounts.

Examples:

```text
house value
car value
manual asset
manual liability
legacy imported net worth category
```

#### TRACKING_POSITIONS

Future-state investment accounts.

Examples:

```text
brokerage
retirement
HSA
```

They track positions by:

```text
ticker
quantity
average basis
cash balance, if needed
```

#### TRACKING_DEBT

Future-state debt accounts.

Examples:

```text
mortgage
car loan
personal loan
```

### 7.3 Budget Account Subtypes

Budget account subtype:

```text
DEPOSIT
CREDIT_CARD
```

Credit cards:

1. Are budget accounts.
2. Can carry negative internal balances.
3. Have linked credit-card payment categories.
4. Participate in the budget through their linked payment category.
5. Are displayed as liabilities when negative.

### 7.4 Category Groups

Category groups are user-configurable containers for categories.

Requirements:

1. Users can create groups.
2. Users can rename groups.
3. Users can reorder groups.
4. Users can hide groups.
5. Users can delete non-system groups if empty.
6. The app imports existing groups from the spreadsheet.
7. The app imports hidden categories and their grouping information where available.

One system group exists by default:

```text
Credit Card Payments
```

Rules:

1. The Credit Card Payments group cannot be deleted.
2. It contains auto-created credit-card payment categories.
3. It may be hidden from display if there are no active credit-card accounts.
4. It may be shown if any active credit-card account exists.

### 7.5 Categories

Category kinds:

```text
STANDARD
CREDIT_CARD_PAYMENT
```

A category is a user-visible budget envelope.

A `CREDIT_CARD_PAYMENT` category is linked by ID to a credit-card budget account. It is where money is reserved to pay down a credit card.

### 7.6 Available to Budget Disambiguation

The name “Available to Budget” appears in two distinct roles. These must never be conflated.

#### Transaction System Category

Use:

```text
TX_AVAILABLE_TO_BUDGET
```

This classifies income or inflow transactions that create unallocated budget money.

Example:

```text
paycheck deposited to checking, categorized as TX_AVAILABLE_TO_BUDGET
```

#### Budget Bucket

Use:

```text
BUCKET_AVAILABLE_TO_BUDGET
```

This is the allocatable system bucket that holds unassigned budget money.

Example:

```text
allocation from BUCKET_AVAILABLE_TO_BUDGET to Grocery category bucket
```

#### Rule

Do not use the same enum value for both concepts.

Bad:

```text
AVAILABLE_TO_BUDGET
```

Good:

```text
TX_AVAILABLE_TO_BUDGET
BUCKET_AVAILABLE_TO_BUDGET
```

### 7.7 System Transaction Categories

Required transaction system categories:

```text
TX_AVAILABLE_TO_BUDGET
TX_STARTING_BALANCE
TX_ACCOUNT_TRANSFER
TX_BALANCE_ADJUSTMENT
```

System transaction categories are not user budget buckets.

### 7.8 Budget Buckets

Budget bucket types:

```text
BUCKET_AVAILABLE_TO_BUDGET
BUCKET_CATEGORY
```

Rules:

1. There is exactly one current `BUCKET_AVAILABLE_TO_BUDGET`.
2. Every category has one `BUCKET_CATEGORY`.
3. Allocations move money between budget buckets.

---

## 8. Versioning Model

### 8.1 SCD2 Validity Intervals

Every editable domain table must use SCD2 validity intervals.

Required versioning columns:

```sql
row_id UUID PRIMARY KEY,
logical_id UUID NOT NULL,
valid_from TIMESTAMPTZ NOT NULL,
valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
created_at TIMESTAMPTZ NOT NULL,
created_by_user_id UUID
```

In concrete tables, use domain-specific logical IDs:

```text
transaction_id
allocation_id
account_id
category_id
group_id
bucket_id
valuation_id
```

### 8.2 Current Rows

A row is current when:

```sql
valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00'
```

Do not add an `is_current` column.

### 8.3 As-Of Rows

A row was valid at app-state time `T` when:

```sql
valid_from <= T AND T < valid_to
```

### 8.4 Edit Semantics

To edit a row:

1. Close the current row by setting `valid_to = now`.
2. Insert a replacement row with the same logical ID and new content.
3. Set replacement `valid_from = now`.
4. Set replacement `valid_to = MAX_TS`.

This must happen in a single database transaction.

### 8.5 Delete/Void Semantics

To delete or void a row:

1. Close the current row by setting `valid_to = now`.
2. Do not insert a replacement row.

### 8.6 No Operation Metadata

Do not require users to provide reasons for edits.

Do not add:

```text
operation
change_reason
closed_reason
closed_operation
```

Diffs are derived by comparing row versions.

---

## 9. Database Schema

### 9.1 Constants

Use shared MAX timestamp:

```sql
TIMESTAMPTZ '9999-12-31 23:59:59+00'
```

All money values are signed 64-bit integers in minor currency units.

```text
$12.34 => 1234
-$12.34 => -1234
```

### 9.2 Import Batch Summary

Only batch-level import metadata is stored.

```sql
CREATE TABLE import_batches (
    import_batch_id UUID PRIMARY KEY,
    spreadsheet_id TEXT NOT NULL,
    spreadsheet_title TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL,
    cutover_at TIMESTAMPTZ NOT NULL,
    summary JSON
);
```

### 9.3 Accounts

```sql
CREATE TABLE accounts (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,

    account_class TEXT NOT NULL, -- BUDGET | TRACKING_BALANCE | TRACKING_POSITIONS | TRACKING_DEBT
    name TEXT NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSON,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

### 9.4 Budget Account Settings

```sql
CREATE TABLE budget_account_settings (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,

    budget_account_type TEXT NOT NULL, -- DEPOSIT | CREDIT_CARD
    linked_payment_category_id UUID,
    display_liability_positive BOOLEAN NOT NULL DEFAULT FALSE,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

Rules:

1. Only `BUDGET` accounts have budget account settings.
2. Credit-card accounts must have `budget_account_type = CREDIT_CARD`.
3. Credit-card accounts must have a linked payment category.
4. Deposit accounts must not have linked payment categories.
5. Credit-card accounts should usually set `display_liability_positive = true`.

### 9.5 Category Groups

```sql
CREATE TABLE category_groups (
    row_id UUID PRIMARY KEY,
    group_id UUID NOT NULL,

    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_deletable BOOLEAN NOT NULL DEFAULT TRUE,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

### 9.6 Categories

```sql
CREATE TABLE categories (
    row_id UUID PRIMARY KEY,
    category_id UUID NOT NULL,

    group_id UUID NOT NULL,
    name TEXT NOT NULL,
    category_kind TEXT NOT NULL, -- STANDARD | CREDIT_CARD_PAYMENT
    sort_order INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    target_amount_minor BIGINT,
    due_date_rule TEXT,
    metadata JSON,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

### 9.7 Budget Buckets

```sql
CREATE TABLE budget_buckets (
    row_id UUID PRIMARY KEY,
    bucket_id UUID NOT NULL,

    bucket_type TEXT NOT NULL, -- BUCKET_AVAILABLE_TO_BUDGET | BUCKET_CATEGORY
    category_id UUID,
    is_allocatable BOOLEAN NOT NULL,
    is_deletable BOOLEAN NOT NULL,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

Rules:

1. There must be exactly one current `BUCKET_AVAILABLE_TO_BUDGET` bucket.
2. Every current category must have one current category bucket.
3. `BUCKET_AVAILABLE_TO_BUDGET` must be non-deletable.
4. Category buckets inherit user visibility from their category.

### 9.8 Transactions

```sql
CREATE TABLE transactions (
    row_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,

    date DATE NOT NULL,
    account_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,

    category_id UUID,
    system_category TEXT,

    status TEXT NOT NULL, -- PENDING | CLEARED
    memo TEXT,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,

    CHECK (
        (category_id IS NOT NULL AND system_category IS NULL)
        OR
        (category_id IS NULL AND system_category IS NOT NULL)
    )
);
```

Rules:

1. Exactly one of `category_id` or `system_category` must be set.
2. Normal spending/income transactions use `category_id`.
3. System transactions use `system_category`.
4. Transfers use `system_category = TX_ACCOUNT_TRANSFER`.
5. Starting balances use `system_category = TX_STARTING_BALANCE`.
6. Income intended for Available to Budget uses `system_category = TX_AVAILABLE_TO_BUDGET`.
7. Transaction status is part of the versioned transaction row.
8. Updating status creates a new transaction version.

### 9.9 Allocations

```sql
CREATE TABLE allocations (
    row_id UUID PRIMARY KEY,
    allocation_id UUID NOT NULL,

    date DATE NOT NULL,
    from_bucket_id UUID NOT NULL,
    to_bucket_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    memo TEXT,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,

    CHECK (amount_minor > 0),
    CHECK (from_bucket_id <> to_bucket_id)
);
```

Rules:

1. Allocations move money between budget buckets.
2. Allocations do not change account balances.
3. Allocations are created through budget UI workflows.
4. Users should not need to edit the allocation table directly.
5. Allocation edits use SCD replacement semantics.

### 9.10 Net Worth Valuations

```sql
CREATE TABLE net_worth_valuations (
    row_id UUID PRIMARY KEY,
    valuation_id UUID NOT NULL,

    account_id UUID,
    raw_name TEXT NOT NULL,
    effective_date DATE NOT NULL,
    amount_minor BIGINT NOT NULL,
    notes TEXT,
    metadata JSON,

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

Rules:

1. Imported net worth rows become valuation facts.
2. Net worth categories that do not map to budget accounts become `TRACKING_BALANCE` accounts.
3. Net worth reporting rows for budget accounts must be ignored in native net worth rollups because those values are derived from the transaction ledger.
4. Future richer tracking account types may take over from imported tracking balance accounts.

### 9.11 Reconciliations

Reconciliation is a fast-follow feature, but schema may be included if simple.

A reconciliation is analogous to a git commit: it records that an account’s app-derived state was reviewed against an external source as of a point in time.

```sql
CREATE TABLE reconciliations (
    reconciliation_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,

    effective_date DATE NOT NULL,
    app_state_timestamp TIMESTAMPTZ NOT NULL,

    external_source TEXT,
    external_balance_minor BIGINT,
    derived_balance_minor BIGINT NOT NULL,
    delta_minor BIGINT NOT NULL,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);
```

No MVP UI is required unless time permits.

---

## 10. Views and Query Semantics

### 10.1 Current Views

Create current views for all SCD tables.

Example:

```sql
CREATE VIEW current_transactions AS
SELECT *
FROM transactions
WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';
```

Required current views:

```text
current_accounts
current_budget_account_settings
current_category_groups
current_categories
current_budget_buckets
current_transactions
current_allocations
current_net_worth_valuations
```

### 10.2 As-Of Queries

As-of queries use:

```sql
valid_from <= :as_of AND :as_of < valid_to
```

These are used for history, diff, and future reconciliation workflows.

### 10.3 Signed Transaction Convention

The native app uses one signed amount column.

```text
positive amount_minor = inflow / increases account balance
negative amount_minor = outflow / decreases account balance
```

Examples:

```text
checking purchase: -5000
checking paycheck: +500000
credit card purchase: -5000
credit card payment received by card: +50000
```

A credit card with debt has a negative internal account balance.

### 10.4 Account Balance Formula

For any current budget account:

```sql
actual_balance_minor =
  COALESCE(SUM(amount_minor), 0)
```

Pending:

```sql
pending_balance_minor =
  COALESCE(SUM(amount_minor) FILTER (WHERE status = 'PENDING'), 0)
```

Cleared:

```sql
cleared_balance_minor =
  COALESCE(SUM(amount_minor) FILTER (WHERE status = 'CLEARED'), 0)
```

Credit cards use the same internal formula.

Display rule:

```text
If budget_account_type = CREDIT_CARD and display_liability_positive = true,
then negative balances may be displayed as positive “owed” amounts.
```

### 10.5 Standard Category Balance Formula

For a standard category `c` with bucket `b`:

```sql
category_available_minor(c) =
    COALESCE((
        SELECT SUM(t.amount_minor)
        FROM current_transactions t
        WHERE t.category_id = c
    ), 0)
  + COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.to_bucket_id = b
    ), 0)
  - COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.from_bucket_id = b
    ), 0)
```

This formula applies across all dates and therefore implements month-to-month rollover.

Spending in prior months remains reflected in the current category balance. Unspent money remains available until moved or spent.

### 10.6 Month Activity Formula

For category `c` during month `[month_start, month_end]`:

```sql
month_activity_minor(c, month) =
  COALESCE((
      SELECT SUM(t.amount_minor)
      FROM current_transactions t
      WHERE t.category_id = c
        AND t.date >= :month_start
        AND t.date <= :month_end
  ), 0)
```

Expenses are negative. Refunds/reimbursements are positive.

### 10.7 Month Budgeted Formula

For category bucket `b` during month `[month_start, month_end]`:

```sql
month_budgeted_minor(b, month) =
    COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.to_bucket_id = b
          AND a.date >= :month_start
          AND a.date <= :month_end
    ), 0)
  - COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.from_bucket_id = b
          AND a.date >= :month_start
          AND a.date <= :month_end
    ), 0)
```

### 10.8 Rollover Formula

Category rollover is not stored separately.

For category `c` with bucket `b`, carried-over balance entering a month is:

```sql
carried_over_minor(c, b, month_start) =
    COALESCE((
        SELECT SUM(t.amount_minor)
        FROM current_transactions t
        WHERE t.category_id = c
          AND t.date < :month_start
    ), 0)
  + COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.to_bucket_id = b
          AND a.date < :month_start
    ), 0)
  - COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.from_bucket_id = b
          AND a.date < :month_start
    ), 0)
```

Then:

```text
category_available =
  carried_over_before_month
+ month_activity
+ month_budgeted
```

This is equivalent to the all-time category balance formula.

### 10.9 Available to Budget Formula

`TX_AVAILABLE_TO_BUDGET` and `BUCKET_AVAILABLE_TO_BUDGET` are distinct.

Available to Budget is the current balance of `BUCKET_AVAILABLE_TO_BUDGET`.

```sql
atb_available_minor =
    COALESCE((
        SELECT SUM(t.amount_minor)
        FROM current_transactions t
        JOIN current_accounts ac ON ac.account_id = t.account_id
        WHERE ac.account_class = 'BUDGET'
          AND t.system_category = 'TX_AVAILABLE_TO_BUDGET'
    ), 0)
  + COALESCE((
        SELECT SUM(t.amount_minor)
        FROM current_transactions t
        JOIN current_accounts ac ON ac.account_id = t.account_id
        WHERE ac.account_class = 'BUDGET'
          AND t.system_category = 'TX_STARTING_BALANCE'
    ), 0)
  + COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.to_bucket_id = :atb_bucket_id
    ), 0)
  - COALESCE((
        SELECT SUM(a.amount_minor)
        FROM current_allocations a
        WHERE a.from_bucket_id = :atb_bucket_id
    ), 0)
```

Rules:

1. Starting balances affect ATB.
2. Starting balances do not count as reportable monthly income.
3. Account transfers do not affect ATB.
4. Spending transactions do not directly affect ATB.
5. Moving money from a category back to ATB increases ATB.
6. Funding a category from ATB decreases ATB.

### 10.10 Reportable Income Formula

For month `[month_start, month_end]`:

```sql
reportable_income_minor(month) =
  COALESCE((
      SELECT SUM(t.amount_minor)
      FROM current_transactions t
      WHERE t.system_category = 'TX_AVAILABLE_TO_BUDGET'
        AND t.amount_minor > 0
        AND t.date >= :month_start
        AND t.date <= :month_end
  ), 0)
```

Do not include:

```text
TX_STARTING_BALANCE
TX_ACCOUNT_TRANSFER
TX_BALANCE_ADJUSTMENT
```

### 10.11 Spending Formula

For month `[month_start, month_end]`:

```sql
spent_minor(month) =
  COALESCE((
      SELECT SUM(-t.amount_minor)
      FROM current_transactions t
      JOIN current_categories c ON c.category_id = t.category_id
      WHERE t.category_id IS NOT NULL
        AND c.category_kind = 'STANDARD'
        AND t.amount_minor < 0
        AND t.date >= :month_start
        AND t.date <= :month_end
  ), 0)
  -
  COALESCE((
      SELECT SUM(t.amount_minor)
      FROM current_transactions t
      JOIN current_categories c ON c.category_id = t.category_id
      WHERE t.category_id IS NOT NULL
        AND c.category_kind = 'STANDARD'
        AND t.amount_minor > 0
        AND t.date >= :month_start
        AND t.date <= :month_end
  ), 0)
```

Do not count:

```text
TX_ACCOUNT_TRANSFER
TX_STARTING_BALANCE
TX_AVAILABLE_TO_BUDGET
TX_BALANCE_ADJUSTMENT
CREDIT_CARD_PAYMENT categories
```

### 10.12 Credit Card Payment Category Formula

Credit-card payment categories must reproduce the source spreadsheet’s operational behavior.

A credit-card payment category `c` is a real category linked by ID to credit-card budget account `a`.

For a credit-card payment category `c` with bucket `b` linked to account `a`:

```sql
credit_card_payment_available_minor(c, b, a) =
    COALESCE((
        SELECT SUM(a2.amount_minor)
        FROM current_allocations a2
        WHERE a2.to_bucket_id = b
    ), 0)
  - COALESCE((
        SELECT SUM(a2.amount_minor)
        FROM current_allocations a2
        WHERE a2.from_bucket_id = b
    ), 0)
  + COALESCE((
        SELECT SUM(-t.amount_minor)
        FROM current_transactions t
        WHERE t.account_id = a
          AND t.category_id IS NOT NULL
          AND t.amount_minor < 0
    ), 0)
  - COALESCE((
        SELECT SUM(t.amount_minor)
        FROM current_transactions t
        WHERE t.account_id = a
          AND t.system_category = 'TX_ACCOUNT_TRANSFER'
          AND t.amount_minor > 0
    ), 0)
```

Interpretation:

1. Manual allocations to the card payment category increase available payment money.
2. Manual allocations away from the card payment category decrease available payment money.
3. Credit-card purchases against normal categories reserve money for payment.
4. Credit-card payments to the card consume reserved payment money.
5. Credit-card payment transfers do not count as spending.
6. Starting balances do not automatically reserve payment money.
7. Preexisting credit-card balances must be funded manually into the payment category.

This formula must be validated against imported credit-card payment categories. If fixture validation shows the formula differs from the source spreadsheet, revise the formula and tests rather than adding hidden credit-card event tables.

Do not create a `credit_card_budget_events` table in v0.1.

Do not backfill generated credit-card events.

### 10.13 Credit Card Refund Behavior

A refund on a credit card is a positive transaction against a normal category.

Example:

```text
account = Reserve Card
category = Grocery
amount_minor = +2500
```

Effects:

1. Card account balance increases.
2. Spending category availability increases.
3. The linked payment category reserve should decrease implicitly through the credit-card payment formula if necessary.

If fixture validation shows explicit refund handling is required, implement it in the credit-card payment formula, not via hidden event tables.

---

## 11. Import Requirements

### 11.1 Supported Tabs

Import only:

```text
Configuration
Transactions
Category Allocation
Net Worth Reports
```

Ignore:

```text
Dashboard
Balances
Account Reports
Category Reports
Spending Reports
Trend Reports
Calculations
Gains over time
Maman's loan
Home scenarios
BackendData
Getting Started Guide
Localization Tools
Colors
```

However, `Balances`, `Dashboard`, and `Calculations` may be read during validation if useful.

### 11.2 Onboarding Flow

When the application starts with an empty database:

1. Show onboarding screen.
2. Prompt user to grant Google Sheets read-only OAuth access.
3. Prompt user to paste Google Sheet URL or ID.
4. Verify the sheet can be read.
5. Show detected sheet title.
6. Import supported tabs.
7. Run validation checks.
8. Show import summary.
9. If validation passes, mark native app as ready.
10. Record import batch summary and cutover timestamp.

### 11.3 Google OAuth

Use OAuth user consent, not service account as the primary UX.

Required Google setup:

```text
Google Cloud project
OAuth consent screen
OAuth client credentials
readonly Google Sheets scope
```

Required scope:

```text
https://www.googleapis.com/auth/spreadsheets.readonly
```

### 11.4 Named Range Discovery And Validation

The importer must use Google Sheets named ranges as the authoritative source for Aspire/dojo import data.

Requirements:

1. Discover named ranges once from spreadsheet metadata.
2. Map actual workbook names into one central importer contract.
3. Read all import data through a small range-access layer.
4. Validate required named ranges before import.
5. Fail loudly on missing ranges, incompatible lengths, or parse failures in meaningful rows.
6. Do not silently guess decorative header positions, row offsets, or visual table bounds.

Expected transaction ranges include names such as:

```text
trx_Dates
trx_Outflows
trx_Inflows
trx_Categories
trx_Accounts
trx_Memos
trx_Statuses
```

Expected category-allocation ranges include names such as:

```text
cts_Dates
cts_Amounts
cts_FromCategories
cts_ToCategories
cts_Memos
```

Expected net-worth ranges include names such as:

```text
ntw_Dates
ntw_Amounts
ntw_Categories
ntw_Notes
```

Expected configuration ranges include semantic names such as:

```text
UserDefAccounts
UserDefCategories
UserDefAmounts
UserDefGoals
NetWorthCategories
NetWorthAssets
HiddenCategories
HiddenAccounts
```

This list is not exhaustive. The importer must inspect the workbook's actual named ranges and map them into the central contract rather than scattering literal strings throughout the codebase.

Header parsing is not the primary import path. If any header parsing remains for a truly optional field with no named range, it must be fallback-only, explicitly documented as such, and must never override or silently disagree with named-range data.

### 11.5 Money Parsing

The importer must convert spreadsheet money strings to signed cents.

Examples:

```text
"$1,300.50" => 130050
"-$15.00" => -1500
"" => null / absent, depending on context
```

For transactions:

```text
inflow => positive amount_minor
outflow => negative amount_minor
```

A transaction row must not have both inflow and outflow populated.

### 11.6 Status Parsing

Map spreadsheet status symbols to:

```text
✅ => CLEARED
🅿️ => PENDING
```

Rows with spacer/status-only markers must be ignored unless they contain valid transaction data.

### 11.7 System Category Mapping

Map source labels to system transaction categories:

```text
Available to budget => TX_AVAILABLE_TO_BUDGET
➡️ Starting Balance => TX_STARTING_BALANCE
↕️ Account Transfer => TX_ACCOUNT_TRANSFER
Balance Adjustment-like source label => TX_BALANCE_ADJUSTMENT
```

### 11.8 Configuration Import

From Configuration, import:

1. Budget accounts.
2. Hidden accounts.
3. Category groups.
4. Categories.
5. Hidden categories.
6. Category monthly amount / target amount where available.
7. Due date rules as raw text.
8. Net worth category names for later valuation import.
9. Credit-card payment categories.
10. Links between credit-card accounts and their payment categories.

Hidden categories and accounts must not be dropped.

### 11.9 Transactions Import

Import every valid transaction row.

Build rows by zipping the transaction named ranges.

Each imported transaction becomes a current SCD row with:

```text
valid_from = import time
valid_to = MAX_TS
```

Do not store row-level spreadsheet provenance.

### 11.10 Category Allocation Import

Import every valid allocation row.

Build rows by zipping the allocation named ranges.

Rules:

1. `Available to budget` maps to the `BUCKET_AVAILABLE_TO_BUDGET` bucket.
2. Normal categories map to their `BUCKET_CATEGORY`.
3. Amounts are positive.
4. From and to buckets must differ.

### 11.11 Net Worth Import

Import net worth rows as valuation facts.

Build rows by zipping the net-worth named ranges.

For each net worth category:

1. If it maps to a budget account, import valuation facts but ignore those rows in native net worth rollups because budget account values are derived from the native transaction ledger.
2. If it does not map to a budget account, create a `TRACKING_BALANCE` account and attach valuations to it.
3. Debt categories may be represented as negative values internally or as positive raw values with metadata, but native net worth rollup must subtract debts correctly.

Do not use “merge” terminology. Native net worth simply ignores Aspire net worth reporting rows for budget accounts where values are directly derivable from transactions.

---

## 12. Import Validation Requirements

### 12.1 No Opening-Balance Fallback

The importer must reconstruct balances from imported source data.

Do not create cutover opening-balance hacks to force parity.

If parity fails, the import is not successful.

### 12.2 Hard Validation Checks

The import must validate:

1. Account actual balances.
2. Account pending balances.
3. Account cleared balances.
4. Available to Budget.
5. Visible category balances.
6. Hidden category balances.
7. Hidden account balances.
8. Credit-card payment category balances.
9. Month activity for visible categories.
10. Month budgeted for visible categories.
11. Rollover / carried-over category values.
12. Category count.
13. Category group count.
14. Account count.
15. Net worth valuation rows imported.
16. Native net worth rollup ignores Aspire net worth reporting for budget accounts.

### 12.3 Validation Tolerance

Money validation tolerance:

```text
0 cents
```

The app must match to the penny.

### 12.4 Import Failure

If validation fails:

1. Show import validation report.
2. Do not mark app as ready.
3. Do not silently create balancing adjustments.
4. Do not mutate the source spreadsheet.
5. Allow retry after code fixes.

---

## 13. Product Flows

### 13.1 First Launch / Onboarding

User opens app with empty DB.

Required flow:

1. App detects no import batch.
2. User sees onboarding screen.
3. User grants Google Sheets read-only access.
4. User pastes Google Sheet URL or ID.
5. App imports data.
6. App runs validation.
7. App shows summary.
8. If validation passes, user lands on budget page.

### 13.2 Budget Dashboard

Budget page must show:

1. Available to Budget.
2. Current month activity.
3. Current month budgeted amount.
4. Carried-over amount.
5. Category groups.
6. Categories in each group.
7. Category available balances.
8. Hidden entities toggle.
9. Credit Card Payments group.
10. Credit-card payment categories.

### 13.3 Fund Category

User can fund a category from ATB.

Effect:

```text
allocation from BUCKET_AVAILABLE_TO_BUDGET to category bucket
```

### 13.4 Move Money Between Categories

Effect:

```text
allocation from source category bucket to destination category bucket
```

### 13.5 Return Money to ATB

Effect:

```text
allocation from category bucket to BUCKET_AVAILABLE_TO_BUDGET
```

### 13.6 Enter Transaction

Fields:

```text
date
account
amount
category or system category
status
memo
```

Rules:

1. Amount is signed.
2. Expense is negative.
3. Inflow is positive.
4. User should not need separate inflow/outflow columns.
5. Category dropdown excludes system-only categories unless system transaction mode is selected.
6. Hidden categories are hidden unless explicitly shown.

### 13.7 Edit Transaction

Users can edit:

```text
date
account
amount
category/system category
status
memo
```

Editing creates a new SCD row with the same `transaction_id`.

### 13.8 Delete Transaction

Deleting closes the current SCD row.

No replacement row is inserted.

### 13.9 Toggle Pending/Cleared

Changing transaction status creates a new SCD row.

Actual account balance must not change.

Pending and cleared balances must change.

### 13.10 Enter Account Transfer

Transfers are not a distinct backend primitive.

A transfer is represented as ordinary transaction rows with:

```text
system_category = TX_ACCOUNT_TRANSFER
```

UI may provide a helper form:

```text
from account
to account
amount
date
memo
status
```

The helper writes two transactions:

```text
source account: negative amount
destination account: positive amount
```

The backend must not require transfer rows to be paired.

### 13.11 Enter Credit-Card Transaction

For a credit-card purchase:

```text
account = credit card
amount = negative
category = spending category
```

Effects:

1. Credit-card account balance decreases.
2. Spending category availability decreases.
3. Linked credit-card payment category behavior follows the formula in Section 10.12.

### 13.12 Enter Credit-Card Payment

Credit-card payments are entered through the transfer helper.

Example:

```text
from account = checking
to account = credit card
amount = positive transfer amount
```

Effects:

1. Checking account decreases.
2. Credit-card account increases.
3. Payment does not count as spending.
4. Payment affects linked credit-card payment category according to Section 10.12.

### 13.13 Manage Categories and Groups

Users can:

1. Create category group.
2. Rename category group.
3. Hide/show category group.
4. Reorder category group.
5. Create category.
6. Rename category.
7. Hide/show category.
8. Move category to group.
9. Reorder category within group.

Credit-card payment categories are normally created by account setup, not manually.

### 13.14 Manage Accounts

Users can:

1. Create account.
2. Rename account.
3. Hide/show account.
4. Mark account inactive.
5. Create credit-card account.

Creating a credit-card account must automatically create/link:

1. Credit-card budget account.
2. Credit-card payment category.
3. Category bucket.
4. Membership in Credit Card Payments group.
5. Budget account settings.

---

## 14. UI Components

### 14.1 Layout Components

Required:

```text
AppShell
TopNav
PageHeader
MetricStrip
Panel
VirtualDataTable
EmptyState
ErrorBanner
LoadingSkeleton
```

### 14.2 Onboarding Components

Required:

```text
OnboardingScreen
GoogleAccessStep
SheetIdInput
ImportPreview
ImportValidationReport
ImportConfirmStep
```

### 14.3 Budget Components

Required:

```text
BudgetMonthSelector
AvailableToBudgetCard
CategoryGroupPanel
CategoryBudgetRow
AllocationPopover
MoneyInput
CategorySelect
HiddenEntitiesToggle
```

### 14.4 Transaction Components

Required:

```text
TransactionEntryBar
VirtualTransactionTable
TransactionStatusToggle
AccountSelect
CategoryOrSystemSelect
TransferEntryDialog
```

### 14.5 Account Components

Required:

```text
AccountList
AccountBalanceCard
AccountDetailPanel
PendingClearedBalanceBreakdown
AccountEditor
```

### 14.6 Category Management Components

Required:

```text
CategoryGroupEditor
CategoryEditor
CategoryReorderControl
CategoryVisibilityToggle
```

---

## 15. API Requirements

### 15.1 Required Endpoints

```text
GET  /api/app/status
POST /api/onboarding/google/start
GET  /api/onboarding/google/callback
POST /api/import/google-sheet
GET  /api/import/status

GET  /api/bootstrap
GET  /api/budget?month=YYYY-MM
POST /api/allocations/fund
POST /api/allocations/move
POST /api/allocations/return-to-atb

GET  /api/transactions
POST /api/transactions
PUT  /api/transactions/{transaction_id}
DELETE /api/transactions/{transaction_id}

POST /api/transfers

GET  /api/accounts
POST /api/accounts
PUT  /api/accounts/{account_id}

GET  /api/categories
POST /api/category-groups
PUT  /api/category-groups/{group_id}
POST /api/categories
PUT  /api/categories/{category_id}

GET  /api/net-worth
```

### 15.2 Bootstrap Endpoint

`GET /api/bootstrap` should return enough state to render the application shell and primary budget page.

Include:

```text
app status
accounts
category groups
categories
budget buckets
current ATB
current budget month summary
recent transactions
import status
```

---

## 16. Testing Requirements

### 16.1 Unit Tests

Required unit tests:

```text
money parsing
date parsing
signed amount conversion from inflow/outflow
status icon mapping
system category mapping
named-range discovery
required named-range validation
compatible named-range length validation
named-range row zipping
category/group extraction
hidden category extraction
hidden account extraction
SCD current query semantics
SCD as-of query semantics
SCD edit semantics
SCD delete semantics
account balance formula
standard category balance formula
month activity formula
month budgeted formula
rollover formula
ATB formula
credit-card payment category formula
net worth budget-account ignore logic
```

### 16.2 Property Tests

Use property-based tests for invariants.

Required properties:

```text
allocations preserve total budget bucket value
moving money A to B decreases A and increases B by same amount
returning money to ATB increases ATB and decreases category
status changes do not change actual account balance
status changes only move value between pending and cleared
editing a transaction changes current state but preserves prior as-of state
deleting a transaction removes it from current state but preserves prior as-of state
cash expense decreases account balance and category availability
income to TX_AVAILABLE_TO_BUDGET increases account balance and BUCKET_AVAILABLE_TO_BUDGET
account transfers do not count as spending
account transfers do not count as income
credit-card purchase decreases card account balance
credit-card purchase decreases spending category availability
credit-card payment transfer decreases deposit account and increases card account
credit-card payment does not count as spending
month-to-month rollover equals all-time category formula
```

### 16.3 Integration and Golden Tests

Use an exported fixture from the copied source spreadsheet.

Required golden tests:

```text
import fixture succeeds
required named ranges are detected
unmapped named ranges are ignored
active categories match expected count
hidden categories import
active accounts match expected count
hidden accounts import
category groups import
transactions import
category allocations import
net worth valuations import
account actual balances match source
account pending balances match source
account cleared balances match source
ATB matches source
visible category balances match source
hidden category balances match source
credit-card payment category balances match source
month activity matches source
month budgeted matches source
rollover/carried-over balances match source
native net worth rollup ignores Aspire net worth reporting for budget accounts
```

### 16.4 Component Tests

Use Vue Test Utils and Vitest.

Required component tests:

```text
MoneyInput parses signed and currency-like values
CategorySelect hides hidden categories by default
CategorySelect can show hidden categories
CategoryOrSystemSelect prevents invalid system category use
BudgetGroupPanel renders categories in order
CategoryBudgetRow opens allocation popover
AllocationPopover submits fund/move/return actions
TransactionEntryBar submits valid transaction payload
TransactionStatusToggle emits pending/cleared update
ImportValidationReport separates hard failures from warnings
HiddenEntitiesToggle reveals hidden categories/accounts
VirtualTransactionTable renders only visible rows plus overscan
```

### 16.5 E2E Tests

Use Cypress sparingly. Tests must be stable and not pixel-perfect.

Required E2E tests:

1. Empty DB onboarding imports fixture and lands on budget page.
2. User funds a category from ATB and sees ATB/category balances update.
3. User enters a cash grocery transaction and sees account/category balances update.
4. User enters a credit-card grocery transaction and sees credit-card/category behavior update.
5. User toggles pending to cleared and sees pending/cleared balances update.
6. User edits a transaction and current values change while history remains available.

Avoid E2E tests for visual details, table sorting minutiae, or exact row order unless controlled by fixture data.

---

## 17. Agent Implementation Warnings

The implementation agent must not make the following mistakes.

### 17.1 Do Not Use React

Vue.js is mandatory.

Do not install or scaffold React.

### 17.2 Do Not Use Full TanStack Suite

Do not use TanStack Router, Query, or Table.

A virtualizer such as TanStack Virtual is allowed.

### 17.3 Do Not Add Generic Event/Postings Model

Use domain-specific tables:

```text
transactions
allocations
accounts
categories
category_groups
budget_buckets
net_worth_valuations
```

### 17.4 Do Not Add Transaction Versions Table

Do not create:

```text
transaction_versions
transaction_status_events
```

Transactions are directly SCD-versioned in one table.

### 17.5 Do Not Add is_current

Current state is determined by:

```text
valid_to = MAX_TS
```

### 17.6 Do Not Add Change Reason Metadata

Do not require user-facing edit reasons.

### 17.7 Do Not Add Row-Level Provenance

Do not add source sheet/row columns to domain tables.

### 17.8 Do Not Create Transfer Table

Transfers are normal transactions with:

```text
system_category = TX_ACCOUNT_TRANSFER
```

The UI may help create two rows, but the backend does not require a transfer primitive.

### 17.9 Do Not Create credit_card_budget_events

Do not create a separate credit-card events table in v0.1.

Credit-card payment category behavior must be derived from linked account/category semantics and validated against the imported fixture.

### 17.10 Do Not Backfill Credit-Card Automation

Imported history must be represented by imported transactions and allocations only.

### 17.11 Do Not Use Opening-Balance Fallbacks

The app must reconstruct operational balances.

Do not insert balancing facts merely to force validation to pass.

### 17.12 Do Not Ignore Hidden Entities

Hidden categories and accounts affect balances and must be imported.

### 17.13 Do Not Double-Count Net Worth

If a net worth category maps to a budget account, ignore Aspire net worth reporting for that budget account in native current net worth.

### 17.14 Do Not Hardcode OAuth Redirect URIs

OAuth redirect URI must come from:

```text
GOOGLE_OAUTH_REDIRECT_URI
```

### 17.15 Do Not Build Deployment Infrastructure

Do not implement Kubernetes, Tailscale, Traefik, or backup cron inside the MVP application.

---

## 18. Future Roadmap

### 18.1 v0.2 Reconciliation

Add reconciliation sessions as git-like commits.

Each reconciliation:

1. Selects account.
2. Shows diff since last reconciliation.
3. Shows pending and cleared records.
4. Lets user clear transactions.
5. Compares derived balance to external balance.
6. Allows adjustment if needed.
7. Stores reconciliation comment/metadata.

### 18.2 v0.3 Net Worth Dashboard

Add:

1. Current net worth.
2. Asset/debt split.
3. Historical net worth chart.
4. Manual valuation entry.
5. Budget-account derived values.
6. Tracking account valuations.

### 18.3 v0.4 Position Tracking

Add:

1. Brokerage and retirement accounts.
2. Position snapshots.
3. Ticker.
4. Quantity.
5. Average basis.
6. Cash balance.
7. Daily price import.
8. Market value rollups.

### 18.4 v0.5 Debt Tracking

Add:

1. Mortgage accounts.
2. Loan accounts.
3. Principal balance snapshots.
4. Optional interest rate.
5. Optional amortization schedule.
6. Debt reconciliation.

### 18.5 v0.6 Reporting

Add:

1. Spending reports.
2. Income reports.
3. Category trends.
4. Account trends.
5. Budget compliance.
6. Cash-flow analytics.

### 18.6 v0.7 Operations

Add:

1. Home infrastructure deployment docs.
2. Optional Kubernetes manifests.
3. Optional Tailscale ingress.
4. Backup and restore automation.
5. DuckDB checkpoint/snapshot process.
6. Split read/write DB access if needed.

---

## 19. MVP Acceptance Criteria

The MVP is complete when:

1. The app runs locally from a laptop.
2. The app uses DuckDB as canonical storage.
3. The frontend uses Vue 3 and TypeScript.
4. React is absent from the frontend stack.
5. The app supports Google OAuth readonly Sheets access.
6. OAuth redirect URI is environment-variable driven.
7. The user can paste a Google Sheet URL or ID.
8. The app imports Configuration, Transactions, Category Allocation, and Net Worth Reports.
9. The app imports visible and hidden categories.
10. The app imports visible and hidden accounts.
11. The app reconstructs account balances to the penny.
12. The app reconstructs ATB to the penny.
13. The app reconstructs visible category balances to the penny.
14. The app reconstructs hidden category balances to the penny.
15. The app reconstructs credit-card payment category balances to the penny.
16. The app reconstructs rollover/carried-over balances to the penny.
17. The app imports net worth snapshots.
18. Native net worth rollup ignores Aspire net worth reporting for budget accounts.
19. The user can view budget categories and balances.
20. The user can fund categories from ATB.
21. The user can move money between categories.
22. The user can return money to ATB.
23. The user can enter transactions.
24. The user can edit transactions.
25. The user can delete transactions.
26. The user can toggle pending/cleared status.
27. The user can enter account transfers through a helper UI.
28. The user can create/edit/hide categories and groups.
29. The user can create/edit/hide accounts.
30. Creating a credit-card account creates a linked payment category.
31. SCD history preserves prior app state.
32. Large transaction lists use DOM virtualization.
33. The UI follows the earth-tone brutalist design system.
34. Unit tests pass.
35. Property tests pass.
36. Golden import tests pass.
37. Component tests pass.
38. Limited Cypress E2E tests pass.

---

## 20. Final Locked Decisions

```text
Use Vue 3, not React.
Use simple Vue reactive state/composables.
Use a virtualizer for large lists.
Do not use full TanStack frontend suite.
Use DuckDB.
Accept DuckDB read/write concurrency limitations for v0.1.
Use signed amount_minor.
Use SCD valid_from/valid_to on domain tables.
Use MAX_TS instead of is_current.
Use domain-specific tables, not generic postings.
Use no operation/change-reason metadata.
Use no row-level spreadsheet provenance.
Use no transfer table.
Use no credit_card_budget_events table.
Use no opening-balance fallback.
Use OAuth user-consent Sheets import.
Drive OAuth redirect URI from environment variables.
Disambiguate TX_AVAILABLE_TO_BUDGET from BUCKET_AVAILABLE_TO_BUDGET.
Import hidden categories and accounts.
Make categories/groups/accounts editable.
Treat credit cards as BUDGET accounts.
Create credit-card payment categories by construction.
Treat credit-card payment categories as real user-visible envelopes.
Import net worth snapshots.
Ignore Aspire net worth reporting for budget accounts in native net worth.
Keep backups/deployment operational, not app MVP.
Use minimalist modern brutalist earth-tone UI.
Roadmap reconciliation, brokerage positions, mortgage/debt tracking, reporting, and operations.
```
