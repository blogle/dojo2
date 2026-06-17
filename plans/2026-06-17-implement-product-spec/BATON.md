# Implementation Baton

## Parent plan

Path: `./plans/2026-06-17-implement-product-spec/PLAN.md`

Current phase: Phase 1 — Design Foundation and Shared Layout

Current work-item status: **Not started**

## Product and repository context

The dojo application is a local-first personal finance tool with a FastAPI + DuckDB backend and Vue 3 frontend. The existing application has working onboarding (fixture/Google Sheet import), budget view, transaction listing/CRUD, account management, category management, and net-worth reporting. The frontend uses a top navigation bar (`TopNav.vue`) and an older custom color/typography token system.

`SPEC.md` defines the canonical product behavior. `DESIGN.md` defines the canonical visual and interaction design system. Both must be used as the sources of truth going forward.

The most immediate gap is that the existing CSS custom properties (`--dojo-bg-off-white`, `--dojo-text-dark-brown`, etc.) and typography (Segoe UI) do not match DESIGN.md tokens (forest green `#34483B`, warm stone `#F4F1E9`, Inter font, 2px radius, compact spacing). The first work item will replace these tokens.

Canonical requirements:
- `SPEC.md` — product behavior
- `DESIGN.md` — visual design, tokens, components

Relevant contributor guidance:
- `CONTRIBUTING.md` — workflow and commands
- `AGENTS.md` — agent routing
- `ARCHITECTURE.md` — runtime structure

## Completed work

None yet.

## Current repository state

- **Branch**: Not specified (working tree has been read-only so far)
- **Working tree**: Clean (no modifications made yet)
- **Last completed task**: N/A
- **Known failing checks**: Unknown (not yet run)
- **Required services**: DuckDB (provisioned by `just api`), Google OAuth (optional)
- **Feature flags**: None
- **Aspire data**: Deterministic fixture available at `fixture://default`

## Capability and dependency status

The capability matrix (`CAPABILITY_MATRIX.md`) documents the full audit. Key findings for the first work item:

- **CSS tokens**: 13 old custom properties exist in `tokens.css`; need replacement with DESIGN.md's 20+ color tokens, 13 typography tokens, 14 spacing tokens, 2 shadow tokens, and 3 transition tokens
- **Global styles**: `main.css` has Tailwind imports, background patterns, and old color usage; needs update
- **Inter font**: Not loaded; currently uses "Segoe UI"
- **Border radius**: Uses browser defaults; needs 2px universal enforcement
- **All existing pages**: Currently render with old tokens; visual changes expected but no functional regressions

## Next work item

**Work Item 1.1: Token System and Global Stylesheet Alignment**

### Objective

Replace the existing CSS custom properties with DESIGN.md-compliant tokens and update the global stylesheet. Add Inter font, enforce 2px border-radius globally, and remove conflicting old styles.

### Scope

- `web/src/dojo/styles/tokens.css` — complete replacement with DESIGN.md tokens
- `web/src/dojo/styles/main.css` — update to use new tokens and DESIGN.md global rules
- Add Inter font via CSS `@import` or `@font-face`
- Apply 2px border-radius globally via `*` selector
- Remove background pattern decoration that conflicts with DESIGN.md

### Explicit non-scope

- No component-level changes to PageHeader, MetricStrip, buttons, inputs, or any other Vue component
- No navigation changes
- No layout changes to AppShell
- No behavior changes
- No backend changes

### Guardrails

- Do not break existing page rendering
- Do not remove Tailwind (it can coexist with custom properties)
- Preserve all existing component functionality
- All DESIGN.md color tokens must be present as `--dojo-*` custom properties

### Relevant files

- `web/src/dojo/styles/tokens.css` (will be rewritten)
- `web/src/dojo/styles/main.css` (will be edited)
- `web/index.html` (may need Inter font link)

### Required validation

- `just check` passes (all backend and frontend tests, lint, typecheck, formatting, architecture checks, migration check)
- Manual visual inspection of Budget, Transactions, Accounts, and Net Worth pages

### Definition of done

1. `tokens.css` contains all DESIGN.md color tokens (primary, primary-hover, primary-active, on-primary, primary-container, on-primary-container, secondary, on-secondary, accent, on-accent, background, surface, surface-raised, surface-muted, surface-selected, on-surface, on-surface-muted, outline, outline-strong, positive, positive-container, warning, warning-container, error, error-container, info, info-container, historical, historical-container, scrim)
2. `tokens.css` contains all DESIGN.md typography tokens (display-lg, headline-lg, headline-md, headline-sm, body-lg, body-md, body-sm, label-lg, label-md, label-sm, caption, metric-lg, metric-md, numeric)
3. `tokens.css` contains all DESIGN.md spacing tokens (micro through nav-expanded)
4. `tokens.css` contains shadow tokens (popover, modal)
5. `tokens.css` contains transition tokens (fast, normal, slow, ease-out)
6. `tokens.css` contains rounded token (all: 2px)
7. `main.css` imports Inter font
8. `main.css` applies 2px border-radius to all elements
9. `main.css` uses new token references instead of hardcoded old colors
10. `just check` passes
11. Existing pages render without functional breakage

## Human decisions required

None.

## Known risks and observations

- Tailwind is currently imported in `main.css`. The new token system should coexist with Tailwind. If conflicts arise, new components should use CSS custom properties directly rather than Tailwind utility classes.
- The existing background pattern in `main.css` uses a gradient + repeating-linear-gradient. This does not match DESIGN.md's "warm stone canvas" aesthetic and should be replaced.
- The Inter font will need to be loaded from a CDN or bundled. Using Google Fonts CDN is the simplest approach for now.
- The old `--dojo-*` tokens are referenced in existing component `<style>` blocks (e.g., `PageHeader.vue`, `TopNav.vue`, `Panel.vue`, `MetricStrip.vue`). We must keep old token names as aliases pointing to new DESIGN.md values so existing components continue to work without modification. This is the strangler pattern for CSS — add new tokens, keep old aliases, migrate component references over time.
- **Alias mapping** (old → new): `--dojo-bg-off-white` → DESIGN.md `background` (#F4F1E9), `--dojo-bg-warm-paper` → DESIGN.md `surface` (#FCFBF7), `--dojo-bg-muted-sand` → DESIGN.md `outline` (#CFC9BC), `--dojo-text-dark-brown` → DESIGN.md `on-surface` (#202923), `--dojo-text-soft-brown` → DESIGN.md `on-surface` (same), `--dojo-text-muted-brown` → DESIGN.md `on-surface-muted` (#616B64), `--dojo-border-brown` → DESIGN.md `outline-strong` (#A9A294), `--dojo-border-tan` → DESIGN.md `outline` (#CFC9BC), `--dojo-green-muted` → DESIGN.md `positive` (#3F6B50), `--dojo-green-dark` → DESIGN.md `primary` (#34483B), `--dojo-green-pale` → DESIGN.md `primary-container` (#DCE7DD), `--dojo-brown-negative` → DESIGN.md `error` (#934B42), `--dojo-brown-warning` → DESIGN.md `warning` (#835C25), `--dojo-ui-font` → Inter stack from DESIGN.md, `--dojo-mono-font` → Inter (remove monospace assumption, use `tnum`/`zero` for financial values).

## Handoff instruction

Read this baton, the parent exec plan (`PLAN.md`), the capability matrix (`CAPABILITY_MATRIX.md`), `SPEC.md`, and `DESIGN.md` before modifying code.
