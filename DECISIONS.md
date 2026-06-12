# Decisions

## 2026-06-10 — Use Nix, direnv, and just for local development

### Context

The project needs a repeatable local environment without depending on host-installed native tooling.

### Decision

Use a Nix flake for the dev shell, `direnv` for automatic shell loading, and `just` for routine commands.

### Consequence

Native dependencies are centralized in `flake.nix`, local and CI workflows stay aligned, and contributors should not install ad hoc system packages for repo work.

## 2026-06-10 — Use Vue 3 instead of React for the frontend skeleton

### Context

The bootstrap needs a minimal frontend framework choice before feature work begins.

### Decision

Use Vue 3 with TypeScript and Vite for the initial frontend skeleton.

### Consequence

Frontend code, tests, and tooling are aligned around Vue patterns, and React-based alternatives are out of scope unless a later decision supersedes this one.

## 2026-06-10 — Use the Three-File Strategy for developer docs

### Context

The repository needs durable technical context without scattering documents across RFC or ADR directories.

### Decision

Use `SPEC.md`, `ARCHITECTURE.md`, and `DECISIONS.md` as the root developer documentation model.

### Consequence

Project scope, current structure, and historical tradeoffs live in predictable places, and RFC/ADR directory trees are explicitly avoided.

## 2026-06-10 — Keep agent guidance minimal and Dojo-specific

### Context

Bootstrap should help coding agents operate safely without creating a large speculative prompt library.

### Decision

Keep `AGENTS.md` concise and limit `agents/` to a small README, an execplan template, and Nix boundary guidance.

### Consequence

Agent context stays compact, custom instructions remain maintainable, and new specialized prompts require repeated evidence of need.

## 2026-06-10 — Add CI during bootstrap and mirror local commands

### Context

The skeleton should validate its environment and workflows before application complexity increases.

### Decision

Add GitHub Actions CI now and make it run the same `just` commands developers use locally, plus the Nix container build.

### Consequence

Local and remote verification stay consistent, and changes to workflow commands should happen in one place instead of diverging between CI and development.

## 2026-06-10 — Adopt self-contained ExecPlans for complex implementation work

### Context

The initial `agents/execplan.md` was too lightweight. It provided a simple planning checklist but did not capture enough context, validation, discoveries, or decision history for a stateless coding agent to safely resume complex work.

### Decision

Adopt a self-contained living ExecPlan workflow for non-trivial implementation tasks. Task-specific plans live under `plans/`, while the reusable skill definition lives in `agents/execplan.md`.

### Consequence

Complex work now has a durable task-local source of truth with progress, discoveries, decision log, validation, and recovery notes. This adds a small amount of process overhead, but only for work where the added structure reduces implementation risk. Durable architectural decisions must still be copied into `DECISIONS.md`.

## 2026-06-10 — Validate imports against a deterministic fixture harness first

### Context

The MVP requires penny-accurate import validation, but the repository does not include real Google credentials or a checked-in copy of the operational spreadsheet.

### Decision

Implement the import pipeline so it can read either a live Google Sheet or a repository fixture, and make the fixture the automated validation source used by tests and local dogfooding.

### Consequence

The app can be exercised end-to-end in CI and local development without secrets, while the live Google path remains available for manual validation once credentials exist. Real-sheet parity is still a follow-up verification step rather than something silently assumed.

## 2026-06-10 — Invoke Ruff through `python -m ruff` inside `uv`

### Context

The standalone Ruff executable exposed in this environment is not consistently runnable through Nix stub-ld boundaries.

### Decision

Run Ruff as `uv run python -m ruff ...` from project workflows instead of depending on a standalone `ruff` binary.

### Consequence

Linting remains hermetic and reproducible under the repo-managed Python environment, and `just` commands no longer rely on a shell-specific Ruff installation detail.

## 2026-06-10 — Make named ranges the authoritative spreadsheet import contract

### Context

Header-scanning visual tables is brittle for long-lived budgeting spreadsheets because decorative rows, layout drift, and optional columns can move independently of the semantic data the app actually needs.

### Decision

Make Google Sheets named ranges the authoritative importer contract. Discover actual workbook names once from metadata, map them into one centralized importer alias table, validate required ranges and compatible lengths up front, and build domain rows by zipping named-range columns.

### Consequence

The importer no longer guesses table bounds from visual headers. Real-sheet compatibility now depends on named-range coverage and validation rather than layout heuristics, and any remaining header parsing must stay fallback-only for clearly optional fields.

## 2026-06-10 — Keep Google OAuth access tokens only in backend memory

### Context

The first OAuth pass wrote granted Google Sheets tokens to a local file. For a local-first budgeting app, that creates avoidable secret persistence and a rougher user trust model than necessary.

### Decision

Keep granted Google OAuth tokens only in backend memory, keyed to an opaque browser-session identifier, and require re-authorization after backend restart instead of persisting tokens to disk.

### Consequence

The Google Sheets import flow is safer by default because tokens are not written to the repository or workstation filesystem by the app. The tradeoff is that OAuth access must be re-established when the backend process restarts.

## 2026-06-11 — Keep named ranges authoritative, but handle shapes explicitly

### Context

Aspire-style Sheets use named ranges for different semantic forms: row-zipped ledger vectors, rectangular configuration/report blocks, and scalar label constants. Treating every named range as a single-column vector breaks valid ranges such as `r_ConfigurationData`.

### Decision

Keep named ranges authoritative, but classify each one explicitly as `COLUMN_VECTOR`, `TABLE_BLOCK`, or `SCALAR_OR_LABEL` in one centralized importer contract before validation or parsing.

### Consequence

The importer can validate and parse ledger vectors, configuration blocks, and scalar symbols correctly without falling back to visual table heuristics or misclassifying rectangular blocks as invalid vectors.

## 2026-06-11 — Ignore unconsumed Aspire named ranges entirely

### Context

Aspire workbooks include many helper, dashboard, UUID, script, broken, and legacy named ranges that are irrelevant to dojo's MVP import path. Reading or validating all of them makes the importer fragile and couples dojo to Aspire internals.

### Decision

Make the importer allowlist-driven: only named ranges in dojo's explicit consumed contract are discovered, fetched, validated, and parsed. Unconsumed named ranges are ignored entirely, even when they are broken.

### Consequence

The importer stops failing on irrelevant workbook internals such as broken UUID ranges, and dojo stays coupled only to the subset of named ranges it actually consumes for MVP parity.

## 2026-06-11 — Derive category hierarchy from `r_ConfigurationData`

### Context

`UserDefCategories` and related flat vectors carry category metadata, but they do not preserve visible category-group boundaries or display ordering. Aspire's rectangular `r_ConfigurationData` block encodes that structure through row symbols.

### Decision

Derive visible category-group membership and ordering by walking `r_ConfigurationData` as a `TABLE_BLOCK`, using consumed scalar named ranges for the group, reportable-category, non-reportable-category, and debt or credit-card-payment row symbols. Keep flat category vectors for metadata only.

### Consequence

dojo now preserves sheet display order and group boundaries without inferring structure from lossy vectors or hardcoded row glyphs. The importer remains allowlist-driven because it consumes only `r_ConfigurationData` plus the scalar symbols needed to interpret that block.

## 2026-06-11 — Classify transaction rows before validating them

### Context

Aspire transaction named ranges can contain structural, reconciliation, pending-staging, and sparse-display rows alongside real amount-bearing transactions. Treating every nonblank row as a transaction caused live-sheet imports to fail on helper rows and inherited-date display patterns.

### Decision

Classify transaction rows before validation. Skip blank, break, reconciliation, helper, and pending staged rows that do not represent committed ledger movement. For real amount-bearing rows, keep strict validation, but allow uncategorized transactions, allow inherited dates from the most recent prior real transaction when the sheet leaves the date cell blank, and continue reading system labels from consumed scalar named ranges.

### Consequence

dojo stays strict about real transaction integrity without coupling itself to every Aspire sheet-display convention. Live imports can now tolerate helper rows and sparse transaction formatting while still failing true malformed transactions.

## 2026-06-11 — Preserve hidden legacy categories referenced by history

### Context

The visible `r_ConfigurationData` block reflects current category structure, but historical transactions and allocations can still reference older hidden categories that no longer appear in that visible block.

### Decision

Keep `r_ConfigurationData` authoritative for visible group membership and ordering, but reconcile post-parse references from transactions and allocations against category metadata. Canonicalize simple reference variants and synthesize hidden inactive categories under an importer-owned hidden group when historical references still exist outside the visible configuration block.

### Consequence

dojo preserves visible sheet structure from `r_ConfigurationData` while still importing historical ledger rows that refer to older hidden categories. This avoids hard failures on live history without reopening broad header- or workbook-wide inference.

## 2026-06-11 — Treat zero-dollar allocations as no-op rows

### Context

The live Aspire allocation vectors include at least one zero-dollar row that is structurally present in the named ranges but does not represent real budget movement.

### Decision

Skip zero-dollar allocation rows during import while continuing to reject negative or malformed allocation amounts.

### Consequence

No-op allocation artifacts no longer block live imports, and dojo still rejects allocation rows that would change balances ambiguously or incorrectly.
