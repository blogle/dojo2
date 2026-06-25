# dojo transactions page screen mockups

This bundle contains the curated, spec-aligned Transactions page mockup screens generated for implementation reference.

## Contents

1. `01-transactions-default.png` — Default Transactions page with compact shell, selected month, inflow/outflow/net metric strip, inline transaction entry form, filter bar, and virtualized ledger.
2. `02-transaction-added-rapid-entry.png` — Successful add state: date/account retained, entry form reset for rapid entry, and success feedback visible.
3. `03-filtered-ledger.png` — Filtered ledger state showing account, date range, category, amount range, status filter, active chips, and matching rows.
4. `04-changes-since-last-reconciliation.png` — Current working-set view using the `Changes since last reconciliation` toggle and changed-record context banner.
5. `05-inline-edit-row.png` — In-place row edit state with compact inline fields and local `Save` / `Cancel` actions.
6. `06-remove-confirmation-modal.png` — Remove confirmation dialog shown over the ledger before marking the active transaction inactive.
7. `07-removed-undo-toast.png` — Removed transaction state with bottom-right `Transaction removed` toast and `Undo` action.
8. `08-oldest-first-logical-order.png` — Display order set to `Oldest first`, illustrating configurable logical entry order without manual pagination.

## Implementation notes

- The column that displays `Pending` / `Cleared` must be named `Status`, not `Reconciliation`.
- `Pending` and `Cleared` are transaction statuses. Reconciliation is a separate audit workflow against an external source of truth.
- Keep the filter or toggle label `Changes since last reconciliation`; that label refers to the current working set since the last successful reconciliation.
- The transaction ledger is virtualized and should use infinite scroll. Do not implement manual pagination controls in the page UI.
- The entry form action button should sit on the same row as the other inputs and use the canonical label `Add`.
- Transaction removal uses the canonical label `Remove`, preserves history by marking the current record inactive, and offers undo through the versioned record model.
