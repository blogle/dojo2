# Capability Matrix

Audit of `SPEC.md` against the current repository state.

## Application Shell and Navigation

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| App shell | Compact expandable left navigation rail | Not implemented | TopNav (horizontal bar) exists in AppShell.vue | N/A | N/A | N/A | No left rail component | 2.1–2.4 | Keep hidden (TopNav current, left rail absent) |
| Nav rail | Collapsed: 56px icons only | Not implemented | No rail component | N/A | N/A | N/A | Not built | 2.1 | Keep hidden |
| Nav rail | Expanded: 208px with labels | Not implemented | No rail component | N/A | N/A | N/A | Not built | 2.1 | Keep hidden |
| Nav rail | Expansion preference persists | Not implemented | No persistence mechanism | N/A | N/A | N/A | No session/local storage handling | 2.2 | Keep hidden |
| Nav rail | Never auto-expand on hover | Not implemented | No rail component | N/A | N/A | N/A | Not built | 2.1 | Keep hidden |
| Nav items | Dashboard, Budget, Transactions, Assets & Liabilities | Partially implemented | TopNav has Budget, Transactions, Accounts, Categories, Net Worth | N/A | N/A | N/A | No Dashboard page, Assets & Liabilities renamed from Accounts | 2.3 | Keep existing top nav for now |
| App utility area | As-of date, attention items, settings, user menu | Not implemented | Not present | N/A | N/A | N/A | Not built | Deferred | Keep hidden |

## Onboarding

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Onboarding | Start empty path | Implemented but inconsistent | `OnboardingScreen.vue` shows sheet input only; no explicit "Start empty" button | `POST /api/import/google-sheet` accepts fixture://default | App status reports ready when data exists | N/A | No Start empty button/flow | 3.1 | Keep existing (needs alignment) |
| Onboarding | Migrate from Aspire path | Implemented but inconsistent | Sheet input defaults to fixture://default, has import confirm step | Google OAuth and sheet import endpoints exist | Import pipeline works with fixture and real sheets | N/A | Missing spec terminology | 3.1 | Keep existing (needs alignment) |
| Onboarding | Migration progress screen | Not implemented | No progress/blocking screen | Backend runs synchronously | N/A | N/A | No progress reporting | 3.2 | Keep hidden |
| Onboarding | Migration completion screen with Details and Continue | Not implemented | No completion screen | Import returns result directly | N/A | N/A | Not built | 3.2 | Keep hidden |
| Onboarding | Details modal with validation summary | Not implemented | ImportValidationReport exists but shown inline, not in modal | Validation report returned in import response | Validation report schema exists | Yes | Modal not built | 3.3 | Keep hidden |
| Onboarding | Failure states | Partially implemented | ErrorBanner shows errors | API returns error details | N/A | N/A | Missing structured failure UI | 3.1 | Keep existing |
| Onboarding | SPEC terminology (Start empty, Migrate from Aspire, Submit, Cancel, Details, Continue to app) | Not conforming | Uses different labels | N/A | N/A | N/A | Terminology not aligned | 3.1 | Keep existing (needs alignment) |

## Core Screens — Dashboard

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Dashboard | Page exists | Not implemented | No Dashboard page/route | No dashboard endpoint | N/A | N/A | Not built | 7.1–7.7 | Keep hidden |
| Dashboard | Net worth, net-worth change, investment change | Not implemented | N/A | No endpoint | N/A | Some data exists in net-worth API | No combined endpoint | 7.1 | Keep hidden |
| Dashboard | Financial trajectory period selector | Not implemented | N/A | No endpoint | N/A | N/A | Not built | 7.1 | Keep hidden |
| Dashboard | Trend chart with hover/drag inspection | Not implemented | N/A | N/A | N/A | N/A | Not built | 7.5 | Keep hidden |
| Dashboard | Spending pressure section | Not implemented | N/A | No endpoint | N/A | N/A | Not built | 7.2 | Keep hidden |
| Dashboard | Upcoming obligations section | Not implemented | N/A | No endpoint | N/A | N/A | Not built | 7.3 | Keep hidden |
| Dashboard | Category watchlist section | Not implemented | N/A | No endpoint | No persistence model | N/A | Not built | 7.7 | Keep hidden |
| Dashboard | Asset/liability watchlist section | Not implemented | N/A | No endpoint | No persistence model | N/A | Not built | 7.7 | Keep hidden |
| Dashboard | Reconciliation attention section | Not implemented | N/A | No endpoint | No persistence model | N/A | Not built | Deferred | Keep hidden |
| Dashboard | Configurable watchlists | Not implemented | N/A | No endpoint | No persistence model | N/A | Not built | 7.7 | Keep hidden |

## Core Screens — Budget

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Budget | Page header with date, ATB, activity, budgeted | Implemented but inconsistent | PageHeader + BudgetMonthSelector + AvailableToBudgetCard + MetricStrip | `GET /api/budget` returns month, atb, summary | DuckDB budget queries work | Yes | MetricStrip doesn't show ATB or budgeted as designed | 4.1 | Expose now |
| Budget | "Spent this month" not displayed separately | Conforming | Not displayed | N/A | N/A | N/A | N/A | N/A | Expose now |
| Budget | Primary actions: Add category, Add category group | Implemented but location differs | Available on separate /categories page, not on Budget page | `POST /api/categories`, `POST /api/category-groups` | Category CRUD works | Yes | Actions not on Budget page itself | 4.1 | Expose now (on Categories page for now) |
| Budget | Historical context (month selector, as-of date) | Partially implemented | Month selector exists; no as-of date support | Month parameter works; no as-of parameter | N/A | N/A | No as-of mode | Deferred | Expose month selector now, as-of hidden |
| Budget | Category hierarchy: CC Payments, user groups, Uncategorized | Implemented but inconsistent | Groups ordered by sort_order; no special CC Payments positioning | Groups returned with sort_order | Category group ordering in DB | Yes | No guaranteed CC Payments priority | 4.2 | Expose now (review ordering) |
| Budget | Empty category groups valid | Implemented | Groups displayed even without categories | Groups returned regardless of category count | DB allows empty groups | Yes | N/A | N/A | Expose now |
| Budget | Reordering mode | Not implemented | Separate Categories page has individual sort-order controls | `PUT /api/categories/{id}` allows sort_order update | Category sort_order in DB | Yes | No dedicated reordering mode UI | 4.3 | Keep hidden (replace Categories page) |
| Budget | Table columns: Category, Goal, Due date, Available, Activity, Budgeted | Implemented but inconsistent | CategoryGroupPanel shows these but not as DESIGN.md table | Budget API returns all needed fields | DB has all needed data | Yes | Column presentation differs | 4.1 | Expose now |
| Budget | Row states: underfunded, due soon, overspent, uncategorized, system, retired | Not implemented | No state indicator components | Budget data includes amounts but no state classification | Category metadata includes target_amount, due_date | Yes | No state badge components | 4.4 | Keep hidden |
| Budget | Category/group detail modal | Not implemented | No detail modal | No specific API for category detail | All data available individually | Yes | No large-detail-modal component | 8.5 | Keep hidden |
| Budget | Goal configuration in detail modal | Not implemented | CategoryEditor shows target_amount, due_date | Category API has target_amount_minor, due_date_rule | Category model has these fields | Yes | No goal editor component | 8.2 | Keep hidden |
| Budget | Funding shortcuts | Not implemented | AllocationPopover exists for manual allocation | `POST /api/allocations/fund` exists | Allocation model works | Yes | No funding dropdown component | 8.3 | Keep hidden |
| Budget | Move funds | Not implemented | No move-funds UI | `POST /api/allocations/move` exists | Allocation model works | Yes | No move-funds-editor component | 8.4 | Keep hidden |
| Budget | Fund category group | Not implemented | No group-level funding | No endpoint | No model | N/A | Not built | Deferred | Keep hidden |
| Budget | Allocation records in Advanced section | Partially implemented | AllocationPopover shows basic allocations | Allocations API works | Allocation model works | Yes | No Advanced section | 8.5 | Keep hidden |
| Budget | Retired categories (Retire/Restore terminology) | Not implemented | Uses is_hidden/is_active with toggle | Category API supports is_hidden, is_active | Category model has is_active field | Yes | Terminology not aligned | 4.5 | Keep hidden |

## Core Screens — Transactions

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Transactions | Page summary with inflow, outflow, net | Not implemented | No summary display | No endpoint returning these grouped | Data available in transactions | Yes | Not built | 5.1 | Keep hidden |
| Transactions | Entry form: date, account, category, amount, direction, memo | Implemented but inconsistent | TransactionEntryBar has date, account, category, amount (± selector), memo, status | `POST /api/transactions` accepts all fields | Transaction model has all fields | Yes | Direction selector exists as ± toggle | 5.1 | Expose now |
| Transactions | Direction defaults to Outflow | Conforming | Defaults to negative (outflow) | N/A | N/A | N/A | N/A | N/A | Expose now |
| Transactions | Post-entry field retention (date/account persist, category/amount/memo reset, focus moves) | Partially implemented | Form resets after submit; field focus behavior unclear | N/A | N/A | N/A | Focus behavior needs review | 5.1 | Expose now (review behavior) |
| Transactions | Enter submits valid transaction | Implemented | Form submission on Enter depends on native form behavior | N/A | N/A | N/A | Needs verification | 5.1 | Expose now |
| Transactions | Canonical input order (immutable entry position) | Implemented | `entry_at` or row_id order used | ORDER BY supported | Immutable ordering exists | Yes | N/A | N/A | Expose now |
| Transactions | Display order configurable (oldest/newest first) | Partially implemented | Default sort_dir=desc; no UI toggle | sort_dir parameter accepted | N/A | N/A | No UI control | 5.1 | Keep hidden (backend supports it) |
| Transactions | Virtualized infinite scroll | Not implemented | Uses pagination buttons (Previous/Next) | offset/limit parameters supported | N/A | N/A | Pagination exists but not infinite scroll | Deferred | Expose current pagination |
| Transactions | Filtering: account, date, date-range, category, amount, reconciliation-state | Not implemented | No filter bar | No filter parameters on transaction endpoint | All filterable data exists | Yes | No filter bar component | Deferred | Keep hidden |
| Transactions | Display active records by default | Conforming | Shows active records | N/A | N/A | N/A | N/A | N/A | Expose now |
| Transactions | Edit flow: select row, edit in place, Save/Enter | Implemented but inconsistent | TransactionEntryBar used for both add and edit; no in-place editing | `PUT /api/transactions/{id}` works | SCD2 versioning works | Yes | In-place row editing not implemented | 5.2 | Expose current (needs alignment) |
| Transactions | Cancel exits editing without new version | Implemented | Cancel resets form | N/A | N/A | N/A | N/A | N/A | Expose now |
| Transactions | Remove with confirmation and undo toast | Partially implemented | Remove works with confirm dialog (browser native); no undo toast | `DELETE /api/transactions/{id}` voids the transaction | SCD2 void works | Yes | No undo toast component | 5.3 | Expose remove, hide undo |
| Transactions | Unreconciled working set filter | Not implemented | No working-set tracking | No reconciliation-status parameter | No reconciliation tracking model | N/A | Not built | 5.4 | Keep hidden |

## Core Screens — Assets & Liabilities

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Assets & Liabilities | Page named Assets & Liabilities | Not conforming | Named "Accounts" | `/api/accounts` | N/A | N/A | Page name differs | 6.1 | Keep current name until refactor |
| Assets & Liabilities | Stacked entity cards | Not implemented | AccountList renders a table, not cards | Account list returns items` | All account data exists | Yes | No stacked-entity-card component | 6.1 | Keep existing table |
| Assets & Liabilities | Add entity wizard | Not implemented | AccountEditor exists as inline form, not wizard | `POST /api/accounts` supports creation | Account model supports all entity types | Yes | No entity-wizard component | 6.2 | Keep existing |
| Assets & Liabilities | Entity detail pages | Not implemented | AccountDetailPanel shows inline detail | No dedicated detail endpoint | All data available | Yes | No detail page/modal | 6.3 | Keep existing inline panel |
| Assets & Liabilities | Pending/Settled settlement states | Implemented | Account shows actual/pending/cleared/display balances | Account API returns all balance types | Ledger supports status tracking | Yes | N/A | 6.4 | Expose now |

## Goal Types

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Goals | One-time goal (amount + date + derived monthly funding) | Not implemented | CategoryEditor shows target_amount_minor, due_date_rule | Category model has these fields stored | Category table has target_amount_minor, due_date_rule | Aspire data may have these populated | No goal type classification or monthly funding derivation | 8.1 | Keep hidden |
| Goals | Recurring goal (amount + frequency + next due date) | Not implemented | No frequency or next_due_date fields | No API for these fields | Schema may not have these fields | Unknown | Missing schema fields | 8.1 | Keep hidden |
| Goals | Discretionary goal (monthly amount, "No due date") | Not implemented | No "No due date" display | No classification | Schema may not distinguish types | Unknown | Missing goal type classification | 8.1 | Keep hidden |

## Reconciliation

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Reconciliation | Working-set model (last reconciliation, changes since) | Not implemented | No working-set tracking | No reconciliation API | No reconciliation persistence | N/A | Not built | 9.1 | Keep hidden |
| Reconciliation | Proposed flow (select, review, resolve, apply) | Not implemented | N/A | N/A | N/A | N/A | Not built | 9.2–9.3 | Keep hidden |
| Reconciliation | Review component with history/diff/value/difference | Not implemented | N/A | N/A | N/A | N/A | Not built | 9.2 | Keep hidden |

## Time Travel

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Time travel | Contextual history per item | Not implemented | No version history component | SCD2 data exists in DB but no history API | SCD2 tables have all history | Yes | No version-history component or API | 10.1 | Keep hidden |
| Time travel | Global as-of mode | Not implemented | No as-of date control | No as-of parameter on endpoints | SCD2 views support as_of query | Yes, via current_ views + scd.py | No as-of API or frontend mode | 10.2–10.3 | Keep hidden |

## Reusable Components

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Components | Compact expandable navigation rail | Not implemented | No component | N/A | N/A | N/A | Not built | 2.1 | Keep hidden |
| Components | Page header | Implemented but inconsistent | PageHeader.vue exists | N/A | N/A | N/A | Doesn't match DESIGN.md | 1.5 | Expose now (will update) |
| Components | Metric strip | Implemented but inconsistent | MetricStrip.vue exists | N/A | N/A | N/A | Doesn't match DESIGN.md | 1.6 | Expose now (will update) |
| Components | Attention panel | Not implemented | No component | N/A | N/A | N/A | Not built | Deferred | Keep hidden |
| Components | Period selector | Not implemented | No component | N/A | N/A | N/A | Not built | Deferred | Keep hidden |
| Components | Trend chart | Not implemented | No component | N/A | N/A | N/A | Not built | 7.5 | Keep hidden |
| Components | Sparkline | Not implemented | No component | N/A | N/A | N/A | Not built | 7.6 | Keep hidden |
| Components | Hierarchical category table | Not implemented | CategoryGroupPanel renders per-group panels, not a unified table | N/A | N/A | N/A | No table component | 4.1 | Keep hidden |
| Components | Virtualized transaction ledger | Implemented but inconsistent | VirtualTransactionTable exists | N/A | N/A | N/A | Uses pagination, not infinite scroll | Deferred | Expose now |
| Components | Filter bar | Not implemented | No component | N/A | N/A | N/A | Not built | Deferred | Keep hidden |
| Components | Stacked entity card | Not implemented | No component | N/A | N/A | N/A | Not built | 6.1 | Keep hidden |
| Components | Large detail modal | Not implemented | No component | N/A | N/A | N/A | Not built | 8.5 | Keep hidden |
| Components | Form modal | Not implemented | No component | N/A | N/A | N/A | Not built | Deferred | Keep hidden |
| Components | Entity wizard | Not implemented | No component | N/A | N/A | N/A | Not built | 6.2 | Keep hidden |
| Components | Goal editor | Not implemented | No component | N/A | N/A | N/A | Not built | 8.2 | Keep hidden |
| Components | Funding dropdown | Not implemented | No component | N/A | N/A | N/A | Not built | 8.3 | Keep hidden |
| Components | Move-funds editor | Not implemented | No component | N/A | N/A | N/A | Not built | 8.4 | Keep hidden |
| Components | State indicators | Not implemented | No component | N/A | N/A | N/A | Not built | 4.4 | Keep hidden |
| Components | Persistent warning banner | Not implemented | No component | N/A | N/A | N/A | Not built | Deferred | Keep hidden |
| Components | Confirmation dialog | Implemented but basic | Uses browser native confirm() | N/A | N/A | N/A | No custom component | 5.3 | Keep hidden (until custom component) |
| Components | Undo toast | Not implemented | No component | N/A | N/A | N/A | Not built | 5.3 | Keep hidden |
| Components | Version history view | Not implemented | No component | N/A | N/A | N/A | Not built | 10.1 | Keep hidden |
| Components | Diff view | Not implemented | No component | N/A | N/A | N/A | Not built | 10.1 | Keep hidden |
| Components | Reconciliation review | Not implemented | No component | N/A | N/A | N/A | Not built | 9.2 | Keep hidden |
| Components | Historical banner | Not implemented | No component | N/A | N/A | N/A | Not built | 10.3 | Keep hidden |
| Components | Retired-items modal | Not implemented | No component | N/A | N/A | N/A | Not built | 4.5 | Keep hidden |

## Acceptance Criteria and Infrastructure

| Spec area | Requirement | Current status | Frontend support | API support | Persistence/model support | Data available | Blocking gap | Planned work item | Exposure decision |
| --------- | ----------- | -------------- | ---------------- | ----------- | ------------------------- | -------------- | ------------ | ----------------- | ----------------- |
| Infrastructure | `GET /health` and `GET /api/health` return healthy | Implemented and conforming | N/A | Both endpoints exist | N/A | N/A | N/A | N/A | Expose now |
| Infrastructure | `GET /api/app/status` and `GET /api/bootstrap` report readiness | Implemented and conforming | Bootstrap is used for app initialization | Both endpoints exist and are bounded | N/A | N/A | N/A | N/A | Expose now |
| Infrastructure | `just setup` works | Implemented and conforming | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Infrastructure | `just api` provisions schema before starting | Implemented and conforming | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Infrastructure | `just web` reaches configured API | Implemented and conforming | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Infrastructure | `GET /api/transactions` accepts offset/limit/sort_by/sort_dir | Implemented and conforming | Client sends these params | Route validates and passes to service | N/A | N/A | N/A | N/A | Expose now |
| Infrastructure | `just check` runs local quality gate | Implemented and conforming | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Infrastructure | `just ci` runs canonical CI | Implemented and conforming | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Design System Token Status

| Token area | DESIGN.md defined | Current status | Gap | Planned work item |
|-----------|-------------------|---------------|-----|-------------------|
| Colors | 20+ color tokens | tokens.css has 13 old brown/tan tokens | Complete replacement needed | 1.1 |
| Typography | 13 type styles with Inter font | "Segoe UI" font, no type scale | Complete replacement needed | 1.1 |
| Spacing | 14 spacing tokens | No systematic spacing scale | Complete replacement needed | 1.1 |
| Shadows | 2 shadow tokens | No shadow tokens defined | Need to add | 1.1 |
| Transitions | 3 transition tokens | No transition tokens defined | Need to add | 1.1 |
| Border radius | 2px universal | Uses browser defaults or old values | Need to enforce 2px | 1.1 |
| Layout components | Stack, Inline, Grid, Surface, Divider | Not built | Need to create | 1.4 |
| Button system | Primary/secondary/tertiary + sm variant | Uses raw `<button>` with old styling | Need component | 1.7 |
| Input fields | Text/select/currency with focus states | Uses raw inputs with old styling | Need component | 1.8 |
