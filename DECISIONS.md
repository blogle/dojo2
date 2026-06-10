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
