# Changelog

## Unreleased

- Added a first-class aggregate validation harness and CLI command so fixture imports and saved real-sheet fetch dumps can be audited with structured labeled checks, cent deltas, source references, and pass/fail notes.
- Corrected Available to Budget semantics to match Aspire's `Dashboard!J3` / `Calculations!B59` behavior, including counting starting-balance inflows without subtracting liability starting-balance outflows.
- Aligned the backend's default budget month with the current calendar month so the default budget view matches Aspire's current dashboard month instead of the last imported ledger month.
- Corrected net-worth rows so every ledger-derived item has an explicit label, normalized duplicate budget-account valuations are ignored in native net worth, and ambiguous duplicate matches fail validation instead of silently double-counting.
- Replaced the ambiguous user-facing `Carried over` label with `Starting Available` on budget tables and removed the top-level carryforward summary metric.
- Corrected budget summary spending totals so hidden-category spending is excluded from the default visible budget summary and only included when hidden entities are explicitly shown.
- Added backend/API/frontend aggregate correctness tests covering account balances, category values, group totals, Available to Budget, hidden-entity behavior, credit-card display behavior, and net worth presentation.
- Tightened aggregate UI labeling by adding backend-provided budget group totals, labeled budget columns, explicit account balance labeling, an accounts-page hidden toggle, and clearer net-worth total/source text.
- Implemented the browser-driven Google OAuth flow in the web app, stopped persisting Sheets access tokens to disk, and now keep granted tokens only in backend memory for the active browser session.
- Corrected the importer's named-range model to support `COLUMN_VECTOR`, `TABLE_BLOCK`, and `SCALAR_OR_LABEL` shapes, including rectangular configuration blocks and scalar sheet symbols.
- Simplified the importer to an explicit allowlist contract so broken or irrelevant Aspire named ranges such as `trx_Uuids` are ignored instead of being validated.
- Corrected category-group import so visible group membership and display ordering come from walking `r_ConfigurationData` with consumed scalar row symbols, while `UserDefCategories` and related flat vectors remain metadata-only.
- Corrected transaction parsing so Aspire helper, reconciliation, break, and other amount-less structural rows embedded in transaction named ranges are classified and skipped instead of failing import, while amount-bearing rows still receive strict validation.
- Corrected live-sheet transaction import to allow uncategorized amount-bearing transactions with blank category cells, and added bootstrap migration support for older DuckDB transaction constraints that previously rejected them.
- Corrected live-sheet transaction import to skip pending staged rows that carry an amount and memo but still have no account or category, instead of treating them as malformed real transactions.
- Corrected live-sheet transaction import to carry forward the prior real transaction date for sparse amount-bearing rows with a blank date cell when the intended date is inherited from the preceding row.
- Corrected live-sheet allocation import to skip zero-dollar no-op rows while still rejecting negative or malformed allocation amounts.
- Added a repository-local live-sheet harness that fetches the allowlisted Google Sheet named ranges into a temporary DuckDB import loop with cached OAuth state for direct importer debugging.
- Refactored the Google Sheets importer to use centralized named-range discovery and validation instead of header-scanning tables.
- Implemented the first working budgeting MVP: DuckDB schema and SCD2 history, fixture-backed onboarding/import validation, budget formulas, API endpoints, Vue workflows for budgeting/accounts/transactions/categories/net worth, and expanded backend/frontend automated coverage.
- Strengthened the ExecPlan agent skill into a self-contained living-plan workflow for complex implementation tasks.
- Bootstrapped project skeleton.
