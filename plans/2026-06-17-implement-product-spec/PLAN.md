# Implementation Plan: Converge dojo toward SPEC.md and DESIGN.md

## Purpose

This plan describes the incremental work items required to converge the existing dojo personal-finance application toward the product behavior described in `SPEC.md` and the visual/interaction design described in `DESIGN.md`. The plan accounts for behavior that already exists, behavior that needs alignment, and gaps requiring new implementation.

## Canonical Sources of Truth

- `SPEC.md` — product behavior, terminology, acceptance criteria
- `DESIGN.md` — visual design tokens, component specs, layout, interactions

## Current Repository State

The application has a working FastAPI + DuckDB backend and a Vue 3 + Vite frontend. It supports:
- Onboarding with deterministic fixture or Google Sheet import via OAuth
- Budget view with Available to Budget, grouped categories, metrics
- Bounded transaction listing with server-side pagination
- Account listing with balances
- Category and account CRUD
- Net-worth reporting with duplicate-valuation deduplication
- SCD2 history for editable records

The current frontend uses a top navigation bar (`TopNav.vue`) instead of the left navigation rail specified in DESIGN.md. Global styles use an older token system (`--dojo-bg-off-white`, etc.) that conflicts with DESIGN.md tokens. Several SPEC.md behaviors (Dashboard, goal types, funding shortcuts, reconciliation, time travel) are not yet implemented.

## Deferred Behavior

The following areas from SPEC.md are explicitly deferred to later phases:
- **Dashboard** (spec sections 296–415) — requires new page, new API endpoints, trend charts, watchlist persistence, and spending pressure calculations
- **Goal types** (spec sections 250–294) — requires one-time/recurring/discretionary goal configuration, goal editor, monthly funding derivation
- **Funding shortcuts** (spec sections 526–538) — requires dropdown button with exact amounts, preview, negative ATB warning
- **Move funds** (spec sections 540–549) — requires move-funds editor UI
- **Fund category group** (spec sections 551–573) — requires allocation ordering logic
- **Reconciliation** (spec sections 764–837) — requires working-set model, diff review, apply workflow
- **Time travel** (spec sections 838–869) — requires contextual history and global as-of mode
- **Undo toast** — requires toast notification system with undo action
- **Confirmations** — requires confirmation dialog component
- **Category/group detail modal** (spec sections 502–524) — requires large detail modal with tabs
- **Retired items** (spec sections 578–587) — requires retire/restore modal
- **Reusable components** (spec sections 871–899) — most are not yet implemented
- **Virtualized infinite scroll** — current transaction page uses pagination buttons, not infinite scroll
- **Filter bar** — not yet implemented

## Implementation Phases

### Phase 1: Design Foundation and Shared Layout

| Work Item | Description | Status |
|-----------|-------------|--------|
| 1.1 | Token system and global stylesheet alignment with DESIGN.md | Planned |
| 1.2 | Contributor documentation update (point to SPEC.md, DESIGN.md) | Planned |
| 1.3 | Application shell layout (compact page canvas, no navigation changes yet) | Planned |
| 1.4 | Shared layout primitives (Stack, Inline, Grid, Surface, Divider) | Planned |
| 1.5 | Page header alignment with DESIGN.md | Planned |
| 1.6 | Metric strip alignment with DESIGN.md | Planned |
| 1.7 | Button system alignment with DESIGN.md | Planned |
| 1.8 | Input field alignment with DESIGN.md | Planned |

### Phase 2: Navigation Rail

| Work Item | Description | Status |
|-----------|-------------|--------|
| 2.1 | Compact expandable left navigation rail component | Planned |
| 2.2 | Navigation item states and persistence | Planned |
| 2.3 | Router integration and page navigation | Planned |
| 2.4 | Remove TopNav, integrate rail into AppShell | Planned |

### Phase 3: Onboarding Alignment

| Work Item | Description | Status |
|-----------|-------------|--------|
| 3.1 | Align onboarding flow with SPEC.md terminology and layout | Planned |
| 3.2 | Add migration progress and completion screens | Planned |
| 3.3 | Add Details modal for validation summary | Planned |

### Phase 4: Budget Alignment

| Work Item | Description | Status |
|-----------|-------------|--------|
| 4.1 | Budget page columns and layout alignment with SPEC.md | Planned |
| 4.2 | Category hierarchy presentation (Credit Card Payments first, Uncategorized last) | Planned |
| 4.3 | Reordering mode implementation | Planned |
| 4.4 | Row state indicators (underfunded, due soon, overspent, etc.) | Planned |
| 4.5 | Retired categories management (retire/restore terminology) | Planned |

### Phase 5: Transactions Alignment

| Work Item | Description | Status |
|-----------|-------------|--------|
| 5.1 | Entry form alignment (direction selector, post-submit behavior) | Planned |
| 5.2 | Edit flow alignment (in-place edit, Save/Enter, Cancel) | Planned |
| 5.3 | Remove and Undo flow | Planned |
| 5.4 | Unreconciled working set indicator | Planned |

### Phase 6: Assets & Liabilities Alignment

| Work Item | Description | Status |
|-----------|-------------|--------|
| 6.1 | Stacked entity cards | Planned |
| 6.2 | Entity wizard for Add item | Planned |
| 6.3 | Detail page component | Planned |
| 6.4 | Settlement state and balance presentation | Planned |

### Phase 7: Dashboard (Backend + Frontend)

| Work Item | Description | Status |
|-----------|-------------|--------|
| 7.1 | Backend financial trajectory API | Planned |
| 7.2 | Backend spending pressure API | Planned |
| 7.3 | Backend upcoming obligations API | Planned |
| 7.4 | Dashboard frontend sections | Planned |
| 7.5 | Trend chart component | Planned |
| 7.6 | Sparkline component | Planned |
| 7.7 | Dashboard configuration (watchlists) | Planned |

### Phase 8: Backend-Supported Vertical Slices

| Work Item | Description | Status |
|-----------|-------------|--------|
| 8.1 | Goal types backend (persistence, derivation) | Planned |
| 8.2 | Goal editor frontend | Planned |
| 8.3 | Funding shortcuts frontend | Planned |
| 8.4 | Move funds frontend | Planned |
| 8.5 | Category detail modal frontend | Planned |
| 8.6 | Watchlist persistence backend | Planned |

### Phase 9: Reconciliation

| Work Item | Description | Status |
|-----------|-------------|--------|
| 9.1 | Reconciliation working-set backend | Planned |
| 9.2 | Reconciliation review frontend | Planned |
| 9.3 | Apply reconciliation flow | Planned |

### Phase 10: History and Time Travel

| Work Item | Description | Status |
|-----------|-------------|--------|
| 10.1 | Contextual history (version history, diff view) | Planned |
| 10.2 | Global as-of mode backend | Planned |
| 10.3 | Global as-of mode frontend | Planned |

## Work Item Detail

### Completion Discipline

Every work item ends with the same baton-update and commit steps before the next item begins.

**Baton update — `./plans/2026-06-17-implement-product-spec/BATON.md`:**

1. Mark the completed work item in `BATON.md` under "Completed work" — include the work-item name, a one-line user-visible outcome, and the commit subject or identifier.
2. Set "Current work-item status" to the next work-item name and note it as **Not started** (or **In progress** if starting immediately).
3. Update "Current repository state" — record the branch, confirm the working tree is clean, and note any known failing checks or relevant service state.
4. Update the capability-matrix exposure decisions that changed as a result of this work item. Add rows to the matrix if new capabilities were discovered. Mark any that became newly exposable or newly deferred.
5. Set "Next work item" to exactly one work-item name from `PLAN.md`. Copy its Objective, Scope, Non-scope, Guardrails, Relevant files, Required validation, and Definition of done into the baton template so the next agent can pick up without reading the full plan.
6. Append any new human decisions, risks, or observations discovered during the work item. If none, leave the section as-is.
7. Remove or resolve any prior human-decisions entries that are no longer relevant.

**Commit:**

1. Create one commit per work item. The commit subject must be a concise imperative statement of the completed outcome (e.g., "Replace CSS custom properties with DESIGN.md token system").
2. Include directly relevant test updates, type changes, and documentation changes in the same commit. Do not mix unrelated work.
3. Leave the working tree clean before starting the next work item.

**Checklist for every work item:**

- [ ] Work item's own definition-of-done items pass
- [ ] Baton updated per the steps above
- [ ] Commit created with concise imperative subject
- [ ] Working tree clean

### Work Item 1.1: Token System and Global Stylesheet Alignment

**Objective**: Replace the existing CSS custom properties with DESIGN.md-compliant tokens and update the global stylesheet.

**User-visible outcome**: The page background, text colors, border colors, and typography change from the old brown/tan palette to the DESIGN.md earth-toned palette (warm stone `#F4F1E9`, forest green `#34483B`, etc.). All existing pages still render correctly with the new colors.

**Scope**:
- Update `web/src/dojo/styles/tokens.css` with DESIGN.md color, typography, spacing, shadow, and transition tokens
- Keep old token names as backward-compatible aliases pointing to new DESIGN.md values (strangler pattern)
- Update `web/src/dojo/styles/main.css` to use new tokens and DESIGN.md rules
- Add Inter font via stylesheet import
- Apply 2px border-radius globally
- Remove or update background patterns that conflict with DESIGN.md
- Add `tnum` and `zero` font-feature-settings on financial values

**Non-scope**:
- No component-level changes (PageHeader, MetricStrip, buttons, inputs remain the same structure)
- No navigation changes
- No layout changes
- No behavior changes

**Affected layers**: Frontend only (styles)

**Known dependencies**: None

**Validation requirements**:
- `just check` passes
- Existing pages render with Aspire-migrated data
- DESIGN.md color tokens are present in CSS
- No regressions in page layout or functionality

**Definition of done**:
- [ ] `tokens.css` contains all DESIGN.md color, typography, spacing, shadow, transition tokens as `--dojo-*` custom properties
- [ ] Old token names exist as backward-compatible aliases referencing new DESIGN.md values
- [ ] `main.css` uses new tokens for base elements; conflicting old hardcoded values are replaced
- [ ] Inter font is loaded from Google Fonts CDN
- [ ] 2px border-radius is applied globally via `*` selector
- [ ] Background gradient/pattern replaced with solid DESIGN.md `background` color
- [ ] Old component styles (PageHeader, TopNav, Panel, MetricStrip, etc.) still render using alias tokens
- [ ] `just check` passes
- [ ] Budget, Transactions, Accounts, and Net Worth pages render without visual breakage

### Work Item 1.2: Contributor Documentation Update

**Objective**: Update AGENTS.md and CONTRIBUTING.md to reference SPEC.md and DESIGN.md as canonical sources of truth.

**Scope**:
- Update AGENTS.md to list DESIGN.md alongside SPEC.md
- Update CONTRIBUTING.md to mention DESIGN.md as visual/interaction source of truth

**Non-scope**: No other documentation changes

**Definition of done**:
- [ ] AGENTS.md lists DESIGN.md in Authoritative Documents
- [ ] CONTRIBUTING.md mentions DESIGN.md where relevant
- [ ] `just check` passes

### Work Item 1.3: Application Shell Layout

**Objective**: Update AppShell to use page-inline and page-block spacing from DESIGN.md, apply background color, and establish the compact page canvas.

**Scope**:
- Update `AppShell.vue` to match DESIGN.md app-shell spec
- Apply `{colors.background}` to shell
- Apply `page-inline`/`page-block` spacing
- Ensure shell uses flex layout with min-height: 100vh
- Add slot-based overlay support for future modal scrim

**Non-scope**: Navigation rail (still uses TopNav, will be replaced in Phase 2)

**Definition of done**:
- [ ] AppShell uses DESIGN.md background color
- [ ] Page canvas has correct inline/block spacing
- [ ] Shell layout is flex with min-height: 100vh
- [ ] Existing pages render correctly within new shell

### Work Item 1.4: Shared Layout Primitives

**Objective**: Create Stack, Inline, Grid, Surface, and Divider components matching DESIGN.md section 8.1.

**Scope**:
- Create `Stack.vue` — vertical flex container
- Create `Inline.vue` — horizontal flex container
- Create `Grid.vue` — CSS grid container
- Create `Surface.vue` — container with variant backgrounds/borders
- Create `Divider.vue` — horizontal/vertical hr

**Non-scope**: Do not replace existing layout usage yet

**Definition of done**:
- [ ] All 5 components exist with DESIGN.md-specified props
- [ ] Components render correctly in test harness
- [ ] `just check` passes

### Work Item 1.5: PageHeader Alignment

**Objective**: Update PageHeader.vue to match DESIGN.md section 8.3 spec.

**Scope**:
- Add subtitle, eyebrow, metadata, primaryActions, sticky props
- Add slots for all DESIGN.md-specified slots
- Apply DESIGN.md typography tokens
- Apply sticky behavior when enabled

**Non-scope**: Do not update all page usages yet (done in later phase)

**Definition of done**:
- [ ] PageHeader has all DESIGN.md props
- [ ] Typography matches DESIGN.md
- [ ] Sticky behavior works
- [ ] Existing page usages still work (may need minimal adjustments)

### Work Item 1.6: MetricStrip Alignment

**Objective**: Update MetricStrip.vue to match DESIGN.md section 8.3 spec.

**Scope**:
- Add MetricItem interface support (delta, auxValue, icon, status, loading, clickable)
- Add scrollable prop
- Apply DESIGN.md typography and spacing
- Add loading skeleton state
- Add delta positive/negative/neutral coloring

**Non-scope**: Do not update all page usages yet

**Definition of done**:
- [ ] MetricStrip supports all DESIGN.md MetricItem fields
- [ ] Loading skeleton renders
- [ ] Delta coloring works
- [ ] Existing usages still work

### Work Item 1.7: Button System Alignment

**Objective**: Create button components matching DESIGN.md section 8.10.

**Scope**:
- Create `DojoButton.vue` with primary, secondary, tertiary variants
- Add compact (sm) variant
- Add hover, active, disabled, loading states

**Non-scope**: Do not replace existing button usage yet

**Definition of done**:
- [ ] DojoButton exists with all DESIGN.md variants
- [ ] All states render correctly
- [ ] `just check` passes

### Work Item 1.8: Input Field Alignment

**Objective**: Create input components matching DESIGN.md section 8.11.

**Scope**:
- Create `DojoInput.vue` — text input with DESIGN.md styling
- Create `DojoSelect.vue` — select with DESIGN.md styling
- Add focus states, placeholder styling

**Non-scope**: Do not replace existing input usage yet

**Definition of done**:
- [ ] DojoInput and DojoSelect exist with DESIGN.md styling
- [ ] Focus states match DESIGN.md
- [ ] `just check` passes

## Ambiguities Requiring Human Input

- **Dashboard formulas**: SPEC.md leaves net financial change and cash-flow result formulas unspecified (section 924). These must be reviewed before implementing Dashboard sections.
- **Retirement vs hiding**: Current app uses `is_hidden`/`is_active`. SPEC.md uses "Retire" and "Restore". The relationship between existing hidden-entity behavior and new retire/restore semantics needs clarification.
- **CC Payment group positioning**: SPEC.md says "Credit Card Payments" group should be first in category hierarchy. Current implementation may need review of how this group is identified and ordered.
- **Category detail modal size**: DESIGN.md specifies 900px max-width for large-detail-modal. SPEC.md says "large modal" for category detail. This seems consistent.

## Design Decisions

- **Tailwind retention**: Current `main.css` imports Tailwind. We will keep Tailwind available but layer DESIGN.md tokens on top, avoiding Tailwind utility classes in new components in favor of CSS custom properties.
- **Component naming**: New design-system components will be prefixed with `Dojo` (e.g., `DojoButton`, `DojoInput`) to distinguish them from eventual native HTML elements and from existing legacy components.
- **Gradual adoption**: Phase 1 establishes tokens and primitives. Existing components continue using their old styles. Phases 3–6 incrementally adopt the new primitives.
