# Product Spec

## Current Product Behavior

dojo currently provides:

- onboarding that can import a deterministic repository fixture or a Google Sheet through the backend OAuth flow
- a DuckDB-backed financial ledger with SCD2 history for editable financial and configuration records
- a budget view with Available to Budget, grouped categories, starting available, month activity, and month budgeted values
- bounded transaction listing with server-side pagination and frontend bounded state
- account listing with actual, pending, cleared, and display balances
- transaction creation, editing, status changes, deletion, and account transfers
- category-group, category, and account management
- net-worth reporting that combines ledger-derived budget-account balances with imported tracking valuations while avoiding double-counting duplicate budget-account valuations

## Acceptance Criteria

- `GET /health` and `GET /api/health` return a healthy application payload.
- `GET /api/app/status` and `GET /api/bootstrap` report readiness without returning a full data dump.
- A fresh repository environment can be set up with `just setup`.
- The API can be started with `just api`, which provisions the DuckDB schema explicitly before starting FastAPI.
- The web app can be started with `just web` and can reach the API through the configured base URL.
- `GET /api/transactions` accepts `offset`, `limit`, `sort_by`, and `sort_dir`, rejects unsupported sort fields, and returns bounded pages with `total` and `has_more` metadata.
- Automated checks exist for repository policy enforcement, fresh database provisioning, SCD2 history behavior, bounded transaction reads, and deterministic fixture-backed financial invariants.
- `just check` runs the normal local quality gate, and `just ci` runs the canonical CI command.

## Current Non-Goals

- production deployment workflows
- background job orchestration
- multi-user authentication and authorization
- browser e2e coverage through a full Cypress suite; the command surface reserves `just test-e2e`, but deterministic Cypress infrastructure is not yet implemented
