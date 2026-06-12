# Prequel Task Specification: Bootstrap the `dojo` Project Skeleton

## 1. Task Summary

Create the initial project skeleton for `dojo`, a local-first personal finance and envelope budgeting application.

This task does **not** implement the budgeting MVP. It creates the minimal repository, development environment, CI, documentation model, and runnable placeholder application needed before implementing the product spec.

The target end state is:

1. A repository named `dojo`.
2. Root-level `web/` and `api/` directories.
3. Vue 3 frontend skeleton in `web/`.
4. FastAPI backend skeleton in `api/`.
5. Source code under the `dojo` namespace.
6. Nix flake development environment.
7. direnv integration.
8. `just` commands for common development workflows.
9. Nix container build target.
10. GitHub Actions CI that verifies the hermetic environment.
11. Compact project documentation using the Three-File Strategy.
12. Minimal agent guidance without context sprawl.
13. A minimal backend server.
14. A minimal frontend static page.
15. Tests proving the skeleton works.

The application name is:

```text
dojo
```

Always use lowercase `dojo`.

---

## 2. Non-Goals

Do not implement the full budgeting application in this task.

Do not implement:

1. Google OAuth behavior.
2. DuckDB schema.
3. Spreadsheet import.
4. Transaction entry.
5. SCD2 tables.
6. Credit card logic.
7. Net worth logic.
8. Reconciliation.
9. Kubernetes manifests.
10. Production deployment.
11. Authentication.
12. Full user documentation.
13. Large custom agent prompt libraries.
14. A full design system beyond initial tokens.

---

## 3. Hard Requirements

### 3.1 Repository Layout

The repository root must contain:

```text
dojo/
  README.md
  AGENTS.md
  SPEC.md
  ARCHITECTURE.md
  DECISIONS.md
  CHANGELOG.md
  flake.nix
  flake.lock
  .envrc
  .env.example
  .gitignore
  .editorconfig
  justfile
  .github/
    workflows/
      ci.yml
  api/
  web/
  docs/
  agents/
```

### 3.2 Required Application Directories

The root must contain exactly these primary application directories:

```text
api/
web/
```

Do not use:

```text
backend/
frontend/
client/
server/
```

### 3.3 Source Namespace

Backend source lives under:

```text
api/src/dojo/
```

Frontend source lives under:

```text
web/src/dojo/
```

### 3.4 Nix Owns Native Tooling

Any binary, compiled, linker-sensitive, or system dependency must be provided by Nix.

Examples:

```text
python
uv
nodejs
pnpm
duckdb CLI
openssl
pkg-config
libffi
zlib
just
mdbook
```

Do not rely on host-installed native tools.

Python and JavaScript package managers may manage language dependencies, but native tooling and compiled dependencies must come from the Nix dev shell.

### 3.5 direnv Integration

The repository must include:

```text
.envrc
```

with:

```sh
use flake
```

Entering the repo with direnv enabled must automatically load the Nix development environment.

### 3.6 Utility Commands

The root `justfile` must expose:

```text
setup
dev
dev-api
dev-web
build
build-api
build-web
test
test-api
test-web
lint
lint-api
lint-web
format
format-check
typecheck
docs
docs-serve
clean
container
```

Running:

```sh
just
```

must list available commands.

### 3.7 Nix Container Target

The flake must expose:

```text
packages.${system}.container
```

The container may initially run only the API skeleton.

`just container` must run:

```sh
nix build .#container
```

### 3.8 Continuous Integration Is Mandatory

The repository must include:

```text
.github/workflows/ci.yml
```

CI must verify the same commands developers run locally:

```sh
just lint
just typecheck
just test
nix build .#container
```

CI must use Nix to provision tooling. Do not install Python, Node, or native dependencies directly with ad hoc GitHub Actions setup steps.

---

## 4. Documentation Model: Three-File Strategy

Avoid scattered developer documentation.

Use exactly three root-level developer-facing project documents:

```text
SPEC.md
ARCHITECTURE.md
DECISIONS.md
```

### 4.1 SPEC.md

`SPEC.md` defines the current MVP boundaries and task-level acceptance criteria.

Rules:

1. It is mostly stable during a milestone.
2. It describes what must be built.
3. It does not record every historical debate.
4. It should be updated only when scope or acceptance criteria change.

### 4.2 ARCHITECTURE.md

`ARCHITECTURE.md` describes the current system state.

Rules:

1. It is mutable.
2. It describes how the code currently works.
3. It must be updated when architecture changes.
4. It should include diagrams or directory explanations if useful.

### 4.3 DECISIONS.md

`DECISIONS.md` is an append-only technical decision log.

It replaces ADR/RFC directories.

Each entry must use:

```markdown
## YYYY-MM-DD — Decision Title

### Context

What problem or tradeoff existed?

### Decision

What did we decide?

### Consequence

What becomes easier, harder, deferred, or forbidden?
```

Rules:

1. Append only.
2. Do not rewrite old decisions except to fix typos.
3. New decisions may supersede old decisions.
4. Use this file to preserve why discarded patterns were rejected.

### 4.4 Forbidden Documentation Structures

Do not create:

```text
rfcs/
rfc/
adr/
adrs/
docs/adr/
docs/adrs/
docs/rfc/
docs/rfcs/
```

### 4.5 User Documentation

User-facing docs remain separate from developer architecture docs.

Create:

```text
docs/
  book.toml
  src/
    SUMMARY.md
    index.md
    quickstart.md
```

These docs must be compilable to static HTML with `mdbook`.

Keep user docs minimal in the skeleton. Full tutorials can be added later.

---

## 5. Minimal Agent Guidance

### 5.1 Goal

Provide enough guidance for opencode/Codex/GPT agents to work safely without flooding their context window.

Do not create a large prompt and skill library during bootstrap.

### 5.2 Required Agent Files

Create only:

```text
agents/
  README.md
  execplan.md
  dojo-nix-boundaries.md
```

### 5.3 agents/README.md

Explain:

1. `AGENTS.md` contains authoritative repo rules.
2. `execplan.md` is used before non-trivial code changes.
3. `dojo-nix-boundaries.md` explains hermetic environment constraints.
4. Prefer standard open-source coding-agent workflows unless they conflict with repo rules.
5. Do not add new custom skills unless repeated Dojo-specific agent failures justify them.

### 5.4 agents/execplan.md

Codify the planning workflow.

Required content:

```markdown
# Execplan

Use before non-trivial implementation work.

## Plan

- Task:
- Files to inspect:
- Files to change:
- Docs to update:
- Tests to add/update:
- Commands to run:
- Risks:

## Rules

- Prefer small, reversible edits.
- Keep docs synchronized with behavior.
- Do not silently change architecture.
- Run the narrowest useful tests first.
- Run broader checks before completion.
- Report tests not run.

## Completion Report

- Changed:
- Tests run:
- Docs updated:
- Remaining risks:
```

### 5.5 agents/dojo-nix-boundaries.md

This is the only custom skill required at bootstrap.

It must explain:

1. Always enter the Nix dev shell.
2. Native dependencies come from Nix.
3. Do not install host-level packages.
4. Do not bypass `just` workflows.
5. If a linker or binary error occurs, fix `flake.nix`, not the host machine.
6. CI must mirror local commands.

### 5.6 AGENTS.md

`AGENTS.md` must be concise.

It must include:

1. Project name.
2. Directory map.
3. Commands to run.
4. Architecture constraints.
5. Documentation maintenance rules.
6. Testing expectations.
7. Forbidden actions.

It must not include the full product spec.

---

## 6. Recommended Repository Tree

Create this structure:

```text
dojo/
  README.md
  AGENTS.md
  SPEC.md
  ARCHITECTURE.md
  DECISIONS.md
  CHANGELOG.md
  flake.nix
  flake.lock
  .envrc
  .env.example
  .gitignore
  .editorconfig
  justfile

  .github/
    workflows/
      ci.yml

  api/
    README.md
    pyproject.toml
    uv.lock
    src/
      dojo/
        __init__.py
        api/
          __init__.py
          main.py
          settings.py
          health.py
    tests/
      test_health.py
      test_settings.py

  web/
    README.md
    package.json
    pnpm-lock.yaml
    index.html
    vite.config.ts
    tsconfig.json
    src/
      main.ts
      dojo/
        App.vue
        router.ts
        api/
          client.ts
        styles/
          tokens.css
          main.css
        components/
          AppShell.vue
          StaticWelcome.vue
    tests/
      App.test.ts

  docs/
    book.toml
    src/
      SUMMARY.md
      index.md
      quickstart.md

  agents/
    README.md
    execplan.md
    dojo-nix-boundaries.md
```

---

## 7. Minimal Application Behavior

### 7.1 Backend

The backend must be a minimal FastAPI app.

Required endpoints:

```text
GET /health
GET /api/health
GET /api/app/status
```

Expected health response:

```json
{
  "status": "ok",
  "app": "dojo"
}
```

Expected app status response:

```json
{
  "app": "dojo",
  "ready": false,
  "mode": "skeleton"
}
```

### 7.2 Frontend

The frontend must be a minimal Vue app served by Vite.

The page must show:

```text
dojo
```

and:

```text
Project skeleton is running.
```

The page must call:

```text
GET /api/app/status
```

and display whether the API is reachable.

### 7.3 Styling

Create initial design tokens in:

```text
web/src/dojo/styles/tokens.css
```

Required tokens:

```css
:root {
  --dojo-bg-off-white: #F4F1EA;
  --dojo-bg-warm-paper: #ECE5D8;
  --dojo-text-dark-brown: #241C15;
  --dojo-text-soft-brown: #4A3728;
  --dojo-border-brown: #8A7664;
  --dojo-green-muted: #3F6B4A;
  --dojo-green-dark: #2E4D36;
}
```

The skeleton page should use these tokens.

---

## 8. Nix Flake Requirements

### 8.1 Dev Shell

The flake must expose:

```text
devShells.${system}.default
```

The dev shell must include:

```text
python
uv
nodejs
pnpm
just
duckdb
mdbook
git
pkg-config
openssl
libffi
zlib
stdenv.cc.cc
```

### 8.2 Container Package

The flake must expose:

```text
packages.${system}.container
```

Acceptable skeleton behavior:

```text
container starts API server on port 8000
```

### 8.3 No Host Tooling Assumption

README and AGENTS.md must state:

```text
Use direnv + nix develop. Do not rely on host-installed Python, Node, uv, pnpm, DuckDB, or mdbook.
```

---

## 9. CI Requirements

### 9.1 Workflow File

Create:

```text
.github/workflows/ci.yml
```

### 9.2 Trigger

CI must run on:

```yaml
on:
  pull_request:
  push:
    branches: [main]
```

### 9.3 Required Jobs

A single job is acceptable for bootstrap.

The job must:

1. Check out the repo.
2. Install Nix using Determinate Systems Nix installer action.
3. Enable Magic Nix Cache.
4. Run local `just` commands through Nix.
5. Build the container target.

### 9.4 Required CI Steps

The workflow must execute:

```sh
nix develop --command just lint
nix develop --command just typecheck
nix develop --command just test
nix build .#container
```

Do not duplicate local logic in CI. CI must call the same `just` commands developers use locally.

### 9.5 Example CI Shape

The final CI may use this shape:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: DeterminateSystems/nix-installer-action@main
      - uses: DeterminateSystems/magic-nix-cache-action@main

      - name: Lint
        run: nix develop --command just lint

      - name: Typecheck
        run: nix develop --command just typecheck

      - name: Test
        run: nix develop --command just test

      - name: Build container
        run: nix build .#container
```

If action versions change later, update this workflow and append a `DECISIONS.md` entry only if the change reflects a policy or tradeoff.

---

## 10. justfile Command Specification

Create a root `justfile`.

### 10.1 setup

Installs language-level dependencies.

Expected:

```sh
cd api && uv sync
cd web && pnpm install
```

### 10.2 dev

Runs API and web dev servers.

Acceptable:

1. Print instructions to run `just dev-api` and `just dev-web` in separate shells.
2. Or run both with simple shell process management.

Prefer simplicity.

### 10.3 dev-api

Runs FastAPI dev server:

```sh
cd api && uv run uvicorn dojo.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 10.4 dev-web

Runs Vite dev server:

```sh
cd web && pnpm dev --host 0.0.0.0 --port 5173
```

### 10.5 test

Runs:

```sh
just test-api
just test-web
```

### 10.6 lint

Runs:

```sh
just lint-api
just lint-web
```

### 10.7 typecheck

Runs backend and frontend type checks.

### 10.8 docs

Builds user-facing HTML docs:

```sh
cd docs && mdbook build
```

### 10.9 docs-serve

Serves docs locally:

```sh
cd docs && mdbook serve
```

### 10.10 container

Builds Nix container target:

```sh
nix build .#container
```

### 10.11 clean

Removes build artifacts only.

Do not delete source files, lockfiles, docs, or user data.

---

## 11. Backend Skeleton Requirements

### 11.1 Python Package

Backend package namespace:

```text
dojo
```

API module path:

```text
dojo.api
```

Entrypoint:

```text
dojo.api.main:app
```

### 11.2 pyproject.toml

Required runtime dependencies:

```text
fastapi
uvicorn
pydantic
pydantic-settings
```

Required dev dependencies:

```text
pytest
httpx
ruff
mypy
```

### 11.3 Settings

Create:

```text
api/src/dojo/api/settings.py
```

Settings must read from environment variables.

At minimum:

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

For skeleton, missing Google OAuth values may be allowed if OAuth is not invoked. The settings object should still define them.

### 11.4 Tests

Backend tests must cover:

1. `/health`.
2. `/api/health`.
3. `/api/app/status`.
4. Settings load from environment.

---

## 12. Frontend Skeleton Requirements

### 12.1 Vue App

Use:

```text
Vue 3
TypeScript
Vite
```

Do not use React.

### 12.2 State

Use simple Vue state/composables.

Do not install:

```text
TanStack Query
TanStack Router
TanStack Table
```

A virtualizer may be added later when large tables exist, but it is not required in this skeleton.

### 12.3 API Client

Create:

```text
web/src/dojo/api/client.ts
```

It must read the API base URL from:

```text
VITE_API_BASE_URL
```

### 12.4 Tests

Frontend tests must verify:

1. The app renders `dojo`.
2. The skeleton status text appears.
3. API status has a loading, reachable, or mocked reachable state.

Mock network calls in tests.

---

## 13. Environment Files

### 13.1 .envrc

Required:

```sh
use flake
```

### 13.2 .env.example

Required:

```env
APP_ENV=development
APP_BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000

DUCKDB_PATH=.local/dojo.duckdb

GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/onboarding/google/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/spreadsheets.readonly

SESSION_SECRET=dev-only-change-me
LOG_LEVEL=debug
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Do not commit real secrets.

---

## 14. Git Ignore Requirements

`.gitignore` must ignore:

```text
.env
.direnv/
.local/
.result
result
node_modules/
dist/
build/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
.DS_Store
docs/book/
```

Do not ignore lockfiles.

---

## 15. EditorConfig Requirements

Create `.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

---

## 16. Root Document Requirements

### 16.1 README.md

The root README is for human developers.

It must include:

1. What `dojo` is.
2. Current project status.
3. Prerequisites:

   * Nix
   * direnv
4. First-time setup.
5. Running API.
6. Running web.
7. Running tests.
8. Building docs.
9. Building container.
10. Repository layout.
11. CI overview.
12. Documentation model.
13. Agent policy summary.

### 16.2 AGENTS.md

`AGENTS.md` is for coding agents and must stay concise.

It must include:

1. Project name and purpose.
2. Directory map.
3. Required commands.
4. Hard constraints.
5. Documentation update rules.
6. Testing expectations.
7. Forbidden actions.

Forbidden actions must include:

```text
Do not use React.
Do not bypass Nix for native tools.
Do not hardcode OAuth redirect URIs.
Do not create ADR/RFC directories.
Do not add large prompt libraries without a repeated observed need.
Do not delete stale docs; update them.
```

### 16.3 SPEC.md

For this bootstrap task, `SPEC.md` should contain this skeleton scope and acceptance criteria in concise form.

It should not contain the full future budgeting MVP.

### 16.4 ARCHITECTURE.md

Initial architecture doc must describe:

1. API skeleton.
2. Web skeleton.
3. Nix dev shell.
4. CI pipeline.
5. Container target.
6. Docs structure.

### 16.5 DECISIONS.md

Initialize with at least these entries:

1. Use Nix + direnv + just for hermetic local development.
2. Use Vue 3 instead of React.
3. Use the Three-File Strategy instead of RFC/ADR directories.
4. Keep agent guidance minimal and Dojo-specific.
5. Add CI at bootstrap to verify local commands and container build.

### 16.6 CHANGELOG.md

Initialize:

```markdown
# Changelog

## Unreleased

- Bootstrapped project skeleton.
```

---

## 17. Completion Criteria

### 17.1 Repository Structure

Complete when:

1. Root files exist.
2. `api/` exists.
3. `web/` exists.
4. `docs/` exists.
5. `agents/` exists.
6. `.github/workflows/ci.yml` exists.
7. Source code is under the `dojo` namespace.

### 17.2 Development Environment

Complete when:

1. `direnv allow` enters the Nix dev shell.
2. Required tools are on `PATH`.
3. `just` lists commands.
4. No host-installed compiled tools are required.

### 17.3 Backend

Complete when:

1. API starts with `just dev-api`.
2. `/health` returns ok.
3. `/api/health` returns ok.
4. `/api/app/status` returns skeleton app status.
5. API tests pass.

### 17.4 Frontend

Complete when:

1. Web app starts with `just dev-web`.
2. Web app renders `dojo`.
3. Web app renders skeleton status.
4. Web app can call API status endpoint.
5. Frontend tests pass.

### 17.5 Docs

Complete when:

1. README exists and is human-focused.
2. AGENTS.md exists and is concise.
3. SPEC.md exists.
4. ARCHITECTURE.md exists.
5. DECISIONS.md exists and has initial decisions.
6. CHANGELOG.md exists.
7. `just docs` builds static HTML docs.
8. `just docs-serve` serves docs locally.

### 17.6 Agent Guidance

Complete when:

1. `agents/README.md` exists.
2. `agents/execplan.md` exists.
3. `agents/dojo-nix-boundaries.md` exists.
4. No large speculative prompt/skill library exists.

### 17.7 CI

Complete when:

1. CI workflow exists.
2. CI installs Nix.
3. CI uses Nix cache action.
4. CI runs `just lint`.
5. CI runs `just typecheck`.
6. CI runs `just test`.
7. CI runs `nix build .#container`.

### 17.8 Build and Test Commands

The following must work locally inside the Nix dev shell:

```sh
just setup
just build
just test
just lint
just format-check
just typecheck
just docs
just container
```

If a command is a skeleton stub, it must still exit successfully and print a clear message.

### 17.9 Container Target

The following must build:

```sh
nix build .#container
```

---

## 18. Implementation Order

Implement in this order:

1. Create repository tree.
2. Add `.envrc`, `.env.example`, `.gitignore`, `.editorconfig`.
3. Add `flake.nix`.
4. Add `justfile`.
5. Bootstrap FastAPI package.
6. Add backend health endpoints and tests.
7. Bootstrap Vue app.
8. Add frontend skeleton page and tests.
9. Add mdbook docs skeleton.
10. Add three-file project docs.
11. Add minimal agent guidance.
12. Add GitHub Actions CI.
13. Add README and CHANGELOG.
14. Run formatting.
15. Run tests.
16. Build docs.
17. Build container.
18. Update DECISIONS.md and CHANGELOG.md.
19. Produce final implementation report.

---

## 19. Expected Final Implementation Report

At completion, report:

```markdown
## Summary

- Bootstrapped dojo project skeleton.
- Added Nix dev environment.
- Added FastAPI skeleton.
- Added Vue skeleton.
- Added CI.
- Added Three-File documentation model.
- Added minimal agent guidance.

## Commands Run

- just setup
- just lint
- just typecheck
- just test
- just docs
- nix build .#container

## Docs Updated

- README.md
- AGENTS.md
- SPEC.md
- ARCHITECTURE.md
- DECISIONS.md
- CHANGELOG.md

## Remaining Work

- Implement budgeting MVP spec.
- Add real Google OAuth flow.
- Add DuckDB schema.
- Add import pipeline.
```

---

## 20. Final Locked Decisions

```text
Project name is dojo.
Use lowercase dojo.
Root app directories are api/ and web/.
Backend namespace is api/src/dojo/.
Frontend namespace is web/src/dojo/.
Use Vue 3, not React.
Use FastAPI for API.
Use DuckDB later as canonical database.
Use Nix for all binary and compiled dependencies.
Use direnv to load the dev environment.
Use just for routine developer commands.
Expose a Nix container build target.
Add GitHub Actions CI at bootstrap.
CI must mirror local just commands.
Use Three-File Strategy: SPEC.md, ARCHITECTURE.md, DECISIONS.md.
Do not create RFC/ADR directories.
Keep AGENTS.md short.
Keep custom agent materials minimal and Dojo-specific.
Initial app is only a minimal API and static Vue page.
```

