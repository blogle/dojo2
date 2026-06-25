# dojo assets & liabilities screen mockups

This bundle contains the curated, spec-aligned Assets & Liabilities mockup screens generated for implementation reference.

## Contents

1. `01-assets-liabilities-default.png` — Default Assets & Liabilities page with compact shell, metric strip, and stacked full-width entity rows grouped into cash and equivalents, investments, tangible assets, credit, and loans.
2. `02-add-item-type-wizard.png` — Add item wizard with the Type step active and supported entity types: budget account, tracking account, investment account, loan, and tangible asset.
3. `03-budget-account-detail.png` — Budget account detail page for Checking with actual balance, pending amount, 30-day change, reconciliation freshness, balance history, filtered transaction ledger, record history, and edit configuration.
4. `04-tracking-account-detail.png` — Tracking account detail page for External Savings with current balance, value history, snapshot history, record history, and edit configuration.
5. `05-loan-detail.png` — Loan detail page for Student Loan with liability-focused metrics, repayment metadata, balance history, recent loan activity, reconciliation state, record history, and edit configuration.
6. `06-account-reconciliation-review.png` — Checking reconciliation review screen showing last reconciled state, current records, source records, proposed result, reconciliation summary, changed/conflicting record review, inclusion toggles, reconciliation history, and Apply reconciliation action.

## Implementation notes

- The page remains named `Assets & Liabilities`.
- Entity rows should be stacked full-width row cards rather than a tile grid.
- The primary page action is `Add item`.
- The Add item wizard first selects the entity type and uses the supported names `budget account`, `tracking account`, `investment account`, `loan`, and `tangible asset`.
- Budget account detail pages include a filtered transaction ledger.
- Tracking account detail pages include snapshot history.
- Pending and Settled are transaction settlement states. Reconciliation remains a separate audit workflow against an external source of truth.
- Use `Changes since last reconciliation`, `Source records`, `Current records`, `Proposed changes`, `Conflict`, `Include`, `Exclude`, `Apply reconciliation`, `Reconciliation history`, and `Restore prior version` consistently in reconciliation surfaces.
- Keep tables and ledgers dense, aligned, and virtualized or infinite-scrolling where applicable. Do not introduce manual pagination controls.
