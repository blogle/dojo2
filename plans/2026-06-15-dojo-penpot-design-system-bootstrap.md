# Dojo Penpot Design-System Bootstrap Plan

## 1. Objective

Bootstrap **Dojo Grounded Ledger** as a reusable Penpot design system consisting of:

1. Atomic design tokens derived from `design.md`.
2. Reusable components and component variants.
3. Composite patterns for tables, charts, navigation, modals, reconciliation, and history.
4. A single tall **Design System Overview** page that mirrors the organization and density of the supplied screenshot.
5. Deterministic validation capable of detecting design drift, hardcoded values, missing variants, duplicate components, and structural errors.
6. Machine-readable build state so an agent can incrementally modify the Penpot file without rebuilding or guessing.

`design.md` remains the authoritative specification for colors, typography, spacing, radii, component appearance, states, and usage rules. 

The screenshot is a **structural and compositional reference**, not a pixel-perfect oracle. Its section ordering, vertical catalog layout, restrained content width, and component-specimen presentation should be reproduced, but individual values must come from `design.md`.

Penpot’s official MCP can inspect and modify pages, layers, components, variants, styles, and tokens. Its current tool surface includes `execute_code`, `high_level_overview`, `penpot_api_info`, `export_shape`, and `import_image`; the local version is preferable when the agent needs direct access to repository files or image assets. ([Penpot Help Center][1])

---

## 2. Definition of Done

The bootstrap is complete only when:

* All source tokens have been represented in Penpot or explicitly classified as non-visual behavior metadata.
* All reusable component families have canonical main components.
* Required visual states are represented as variants or clearly named state specimens.
* Every overview-page example uses a component instance rather than a detached copy.
* No managed component contains unapproved hardcoded colors, spacing, typography, radii, or shadows.
* The overview page contains every major component family from `design.md`.
* Automated validation returns zero blocking errors.
* A visual baseline has been exported after human approval.
* The design-system file can be published as the source library for future screen and flow work.
* The machine-readable build state contains stable Penpot IDs for all managed pages, boards, components, variant sets, and important specimens.

Runtime behavior such as virtualization, infinite scrolling, timers, drag-to-measure calculations, and hover-to-pause cannot be fully implemented as design-system logic. Penpot should represent their **visual states, transitions, and annotations**, while the application remains responsible for runtime behavior.

---

## 3. Source-of-Truth Hierarchy

Resolve conflicts in this order:

1. `design.md`
2. Generated source manifest
3. Approved Penpot component master
4. Overview-page specimen
5. Screenshot reference

Rules:

* Never infer a new color, type size, radius, control height, or semantic state from the screenshot.
* Never modify `design.md` merely to match an implementation mistake in Penpot.
* Generated manifests are derivative artifacts and must not be hand-edited.
* Missing or contradictory source information becomes a named `TODO`; it must not be silently invented.
* Existing application implementation may be consulted for content and composition, but it does not override the design specification.

---

## 4. Managed Artifacts

The coding agent should maintain these files alongside the source specification:

```text
penpot/
├── source-manifest.json
├── tokens.dtcg.json
├── component-catalog.json
├── validation-rules.json
├── build-state.json
├── validation-report.json
└── snapshots/
    ├── overview-approved.png
    ├── foundations-approved.png
    ├── components-approved.png
    └── qa-approved.png
```

### `source-manifest.json`

Normalized representation of the YAML frontmatter and enforceable prose rules.

Contains:

* Source file hash
* Canonical token names and values
* Alias graph
* Component property mappings
* Component state inventory
* Explicit exceptions
* Unsupported or behavioral properties
* Overview section order

### `tokens.dtcg.json`

Generated W3C DTCG-compatible token bundle. Penpot supports DTCG-formatted tokens, aliases, mathematical relationships, token sets, themes, and JSON import/export. ([Penpot Help Center][2])

### `component-catalog.json`

For every component:

```json
{
  "name": "control/button",
  "source": "components.button-primary",
  "atomicLevel": "atom",
  "variantAxes": {
    "Level": ["Primary", "Secondary", "Tertiary"],
    "Size": ["Default", "Small"],
    "State": ["Default", "Hover", "Active", "Disabled", "Loading"]
  },
  "requiredCombinations": [],
  "disallowedCombinations": [],
  "dependencies": [
    "primitive/icon",
    "primitive/text/label"
  ],
  "overviewSection": "Controls",
  "status": "pending"
}
```

### `validation-rules.json`

Machine-readable policy rather than prose-only instructions.

### `build-state.json`

Records:

* Source hash used for the build
* Penpot file ID
* Page and board IDs
* Main component IDs
* Variant set IDs
* Last successful phase
* Last validation timestamp
* Approved snapshot hashes
* Known warnings and manual-review items

No mutation should rely solely on a fuzzy name search after an ID has been established.

---

## 5. Penpot File Architecture

Create the following pages:

```text
00 · Design System Overview
01 · Foundations
02 · Components
03 · Patterns
90 · QA
99 · Scratch
```

### `00 · Design System Overview`

Human-facing catalog. Contains only:

* Documentation frames
* Section labels
* Component instances
* Explanatory annotations
* A small number of non-component chart or token specimens where appropriate

It must not contain source component masters.

### `01 · Foundations`

Contains:

* Color token specimens
* Typography scale
* Numeric typography examples
* Spacing scale
* Size and control-height scale
* Radius specimen
* Border and divider specimens
* Shadow specimens
* Icon guidance
* Transition documentation
* Accessibility pairings

### `02 · Components`

Contains canonical main components and variant sets for:

* Layout primitives
* Controls
* Navigation
* Data display
* Tables
* Feedback
* Overlay primitives

### `03 · Patterns`

Contains larger compositions:

* App shell
* Navigation rail
* Attention panel
* Trend-chart states
* Hierarchical table
* Transaction ledger
* Modal compositions
* Wizard
* Goal editor
* Move-funds editor
* Diff view
* Reconciliation review
* Version history
* Retired-items modal

### `90 · QA`

Contains mechanically testable specimens:

* All variant matrices
* Resize tests
* Long-label tests
* Empty and loading states
* Semantic pairings
* Compact and mobile touch-target tests
* Component nesting tests
* Instances with text overrides
* Historical, warning, error, and reconciliation states displayed together

### `99 · Scratch`

Disposable work only. Nothing on this page may be referenced by the overview or published library.

Penpot recommends clear page/board purposes, hierarchical naming, functional component groupings, token-derived values, shallow component trees, and flex/grid layouts rather than chaotic free-positioned canvases. ([Penpot Help Center][3])

---

## 6. Token Architecture

Use three tiers.

### Tier 1: Core values

Implementation-oriented raw values:

```text
core.color.forest.700
core.color.stone.050
core.color.clay.500
core.dimension.2
core.dimension.4
core.dimension.8
core.dimension.12
core.dimension.16
core.dimension.24
core.dimension.32
core.dimension.48
core.font.family.inter
core.font.weight.400
core.font.weight.500
core.font.weight.600
core.font.weight.700
```

These should not normally be applied directly to components.

### Tier 2: Semantic tokens

Preserve the terminology from `design.md`:

```text
colors.primary
colors.primary-hover
colors.background
colors.surface
colors.surface-raised
colors.on-surface
colors.positive
colors.warning
colors.error
colors.info
colors.historical

spacing.micro
spacing.xs
spacing.sm
spacing.md
spacing.lg
spacing.xl
spacing.2xl
spacing.3xl
spacing.row-height-compact
spacing.row-height-default

rounded.all

typography.body-md
typography.label-sm
typography.metric-lg
typography.numeric

shadows.popover
shadows.modal
```

Values should alias Tier 1 wherever practical.

### Tier 3: Component tokens

Examples:

```text
component.button.primary.background
component.button.primary.foreground
component.button.height.default
component.button.radius
component.input.background
component.input.border.color
component.input.border.width
component.table.header.background
component.table.row.height
component.modal.shadow
```

These alias semantic tokens and make future component-specific changes intentional.

Penpot’s own design-system guidance recommends global, semantic, and component token tiers, with component geometry and styling derived from tokens rather than manual values. ([Penpot Help Center][3])

### Token sets

Use deterministic ordering:

```text
01-core
02-semantic
03-component
```

Use one active theme:

```text
Theme group: Mode
Theme: Grounded Light
```

Do not invent a dark theme. The architecture may support it later without providing unsourced values.

Penpot token-set order is cascading: later active sets can override earlier sets. Unique token names should therefore be used unless an override is deliberate and documented. ([Penpot Help Center][2])

### Source-property mapping

| Source property                               | Penpot representation                         |
| --------------------------------------------- | --------------------------------------------- |
| `backgroundColor`, `textColor`, `strokeColor` | Color token                                   |
| `height`, `width`, `gap`, `padding`, `size`   | Dimension token                               |
| `rounded`                                     | Border-radius token                           |
| `opacity`                                     | Opacity token                                 |
| `typography`                                  | Typography composite token                    |
| `shadow`                                      | Shadow composite token                        |
| `border`                                      | Decomposed stroke width, color, and placement |
| `fontWeight`                                  | Typography token or numeric subtoken          |
| `position`, `display`, `zIndex`, `cursor`     | Behavioral metadata only                      |
| `transition`, `animation`, keyframes          | Annotation and implementation metadata        |
| Runtime callbacks and events                  | Component documentation only                  |

Penpot supports token binding for sizing, position, radius, spacing, typography properties, stroke width, shadows, and related numeric fields. ([Penpot Help Center][2])

---

## 7. Component Naming and Layer Naming

### Library names

Use slash-separated functional names:

```text
primitive/layout/stack
primitive/layout/inline
primitive/layout/grid
primitive/surface
primitive/divider

control/button
control/input
control/select
control/currency-input
control/filter-chip
control/period-preset
control/state-badge

navigation/nav-item
navigation/navigation-rail

data/metric-item
data/metric-strip
data/stacked-entity-card
data/sparkline
data/trend-chart

table/header-cell
table/body-cell
table/category-row
table/ledger-row
table/hierarchical-category-table
table/transaction-ledger

feedback/tooltip
feedback/toast
feedback/persistent-banner
feedback/historical-banner

overlay/modal-shell
overlay/form-modal
overlay/confirmation-dialog
overlay/entity-wizard

specialized/funding-dropdown
specialized/goal-editor
specialized/move-funds-editor
specialized/diff-view
specialized/reconciliation-review
specialized/version-history
specialized/retired-items-modal
```

### Internal layers

Name by role:

```text
container
background
border
leading-icon
label
supporting-text
value
delta
status
trailing-icon
actions
divider
```

Never use generated names such as `Rectangle 23`, `Group 11`, or `Text 8`.

Shared layers across variants must retain the same name, object type, and hierarchy level so instance overrides survive variant switching. Penpot variants use explicit properties and values, and connected layer consistency is required to preserve overrides. ([Penpot Help Center][4])

---

## 8. Atomic Component Strategy

A supporting atom should be promoted into a reusable component only when at least one of these is true:

* It appears in two or more documented components.
* It has its own documented state matrix.
* It has semantic meaning outside its parent.
* It needs independent replacement or overrides.
* It is directly named in `design.md`.

Otherwise, keep it as a named internal layer.

This avoids creating a huge library of meaningless one-off rectangles and wrappers.

### Atomic layers

* Text roles
* Icon wrapper
* Divider
* Surface
* State dot
* Button
* Input
* Select
* Currency input
* Badge
* Filter chip
* Period preset
* Reconciliation inclusion control
* Table cell
* Sparkline

### Composites

* Nav item
* Metric item
* Form field
* Attention item
* Table row
* Banner
* Toast
* Tooltip
* Funding split button
* Version-history entry

### Organisms and patterns

* Navigation rail
* Page header
* Metric strip
* Filter bar
* Attention panel
* Trend chart
* Tables
* Modals
* Wizard
* Editors
* Reconciliation review
* Version history
* App shell

---

## 9. Required Variant Families

Use Penpot property naming such as:

```text
Level=Primary, Size=Default, State=Default
```

Penpot supports variant properties and values, including boolean pairs such as `true/false`. ([Penpot Help Center][4])

| Component             | Variant axes                               |
| --------------------- | ------------------------------------------ |
| Button                | `Level`, `Size`, `State`, optional `Icon`  |
| Input                 | `Kind`, `State`, `Label`, `SupportingText` |
| State badge           | `Semantic`, `Size`, optional `Icon`        |
| Nav item              | `Mode`, `State`, `Badge`                   |
| Period preset         | `State`                                    |
| Filter chip           | `State`, `Removable`                       |
| Metric item           | `State`, `Delta`, `Status`, `Clickable`    |
| Attention panel       | `State`, `Content`                         |
| Stacked entity card   | `State`, `Delta`, `Status`, `Trend`        |
| Sparkline             | `Trend`, `Area`, `EndDot`                  |
| Trend chart           | `State`, `SeriesCount`                     |
| Table row             | `Kind`, `State`, `Depth`, `Edited`         |
| Ledger                | `State`                                    |
| Banner                | `Semantic`, `Dismissible`, `Actions`       |
| Toast                 | `Semantic`, `Undo`                         |
| Modal shell           | `Size`, `Header`, `Footer`                 |
| Confirmation dialog   | `Semantic`                                 |
| Wizard step           | `State`                                    |
| Funding dropdown      | `State`                                    |
| Diff view             | `Layout`                                   |
| Reconciliation item   | `Included`, `Conflict`                     |
| Version-history entry | `State`, `Restorable`                      |

Do not generate a full Cartesian product when combinations are nonsensical. `component-catalog.json` must enumerate required and disallowed combinations explicitly.

Example:

```json
{
  "component": "control/button",
  "disallowedCombinations": [
    {
      "Level": "Tertiary",
      "Size": "Small",
      "State": "Loading"
    }
  ]
}
```

---

## 10. Design System Overview Page

Create a single vertically flowing board named:

```text
Overview / Grounded Ledger
```

Recommended geometry:

```text
Board width: 1440px
Content origin: x=96px
Content width: 1040–1120px
Page background: colors.background
Section gap: spacing.3xl
Internal specimen gap: spacing.xl
```

The deliberately narrow content column and open right side should preserve the visual character of the reference screenshot.

### Section order

#### Header

* `Dojo Design System`
* `Grounded Ledger`
* Version and source hash
* Brief atmosphere description
* “Generated from design.md” indicator
* Last validation status

#### 1. Foundations

* Typography specimen table
* Financial numeric examples
* Complete color swatch matrix
* Semantic pairings
* Spacing bars
* Control and row heights
* Radius specimen
* Border treatments
* Popover and modal shadow specimens
* Transition reference

#### 2. Layout Primitives

* Stack
* Inline
* Wrapping inline
* Two- and three-column grid
* Surface variants
* Divider variants

#### 3. Navigation

* Collapsed navigation rail
* Expanded navigation rail
* Default, hover, selected, and badge states

#### 4. Controls and Page Data

* Button grammar
* Inputs and selects
* Filter chips
* Period selector
* Page header
* Metric strip
* Attention panel
* Stacked entity cards
* State badges
* Sparklines
* Trend-chart states

#### 5. Historical and Persistent States

* Historical banner
* Info banner
* Warning banner
* Error banner
* Multiple simultaneous state example

#### 6. Tables

* Hierarchical-category table
* Group and child rows
* Selected and edited rows
* Transaction ledger
* Loading skeleton
* Inline editing
* Conflict treatment

#### 7. Modals and Wizards

Present modals as contained static specimens rather than allowing their scrims to cover the entire catalog:

* Large-detail modal
* Form modal
* Confirmation dialog
* Entity wizard

#### 8. Feedback

* Tooltip
* Info, positive, warning, and error toasts
* Undo action
* Validation message
* Error message

#### 9. Specialized Components

* Funding dropdown open and closed
* Goal editor
* Derived-value box
* Move-funds editor
* Live balance preview

#### 10. History and Review

* Diff layouts
* Reconciliation summary and item states
* Version history
* Retired-items modal

Each specimen must include:

* Component name
* Variant or state label
* Instance
* Short behavioral annotation where behavior cannot be expressed visually
* Optional token references for especially important dimensions

---

## 11. Agentic Execution Phases

## Phase 0 — Capability and Safety Preflight

The agent must:

1. Call `high_level_overview`.
2. Call `penpot_api_info` for pages, tokens, components, variants, layouts, and export operations.
3. Verify the active file and focused page.
4. Determine whether token creation and binding are available through the current MCP/plugin version.
5. Confirm Inter is available.
6. Inventory existing pages, tokens, styles, and components.
7. Produce a dry-run change report before writing.

Penpot MCP follows the currently focused page in the active Penpot tab, so page identity must be checked before every mutation batch. ([Penpot Help Center][1])

**Blocking conditions:**

* Wrong Penpot file
* Unexpected focused page
* Existing managed pages with unrecognized ownership
* Missing write capability
* Source parse failure
* Unresolved token aliases
* Duplicate canonical token names

## Phase 1 — Compile Source Artifacts

* Parse YAML frontmatter.
* Normalize all token references.
* Split visual and behavioral properties.
* Produce DTCG token JSON.
* Produce component catalog.
* Produce validation rules.
* Calculate source hash.
* Fail on dangling references or duplicate names.

No Penpot writes occur in this phase.

## Phase 2 — Create Foundations

* Create pages.
* Create token sets and theme.
* Create color, dimension, radius, opacity, typography, and shadow tokens.
* Create the Foundations board.
* Bind all specimens to tokens.
* Run token and contrast validators.
* Export a foundations snapshot.

## Phase 3 — Create Primitives and Controls

Build in dependency order:

1. Layout primitives
2. Surface and divider
3. Icon wrapper and state dot
4. Buttons
5. Inputs and selects
6. State badges
7. Chips and period presets
8. Table cells
9. Sparkline

Validate each family before starting the next.

## Phase 4 — Create Navigation and Data Components

* Nav item
* Navigation rail
* Page header
* Metric item and strip
* Filter bar
* Attention item and panel
* Stacked entity card
* Trend chart

## Phase 5 — Create Complex Patterns

* Tables
* Modal shell and modal compositions
* Wizard
* Feedback systems
* Specialized editors
* Diff and reconciliation
* Version history
* Retired-items modal
* App shell

## Phase 6 — Assemble Overview

* Create section shells.
* Insert instances only.
* Populate realistic financial sample data.
* Match screenshot section order and catalog density.
* Add annotations for non-visual behavior.
* Confirm no source masters exist on the overview page.

## Phase 7 — QA and Publish

* Build the QA matrix.
* Run all structural and visual validators.
* Export snapshots.
* Perform one human visual review.
* Establish approved visual baselines.
* Publish the file as the reusable design-system library.

---

## 12. Mutation Guardrails

### Small-batch rule

Each write batch may change only one of:

* One token set
* One component family
* One overview section
* One validation repair category

Do not run “create the entire design system” as a single mutation.

### Focus guard

Before each write:

```text
assert current_file_id == build_state.penpot_file_id
assert current_page_id == expected_page_id
```

Stop rather than attempting to recover by guessing.

### Managed-region guard

The agent owns only:

* The six named pages
* Objects whose IDs appear in `build-state.json`
* Objects created during the current uncommitted batch

Anything else is read-only.

### Exact-ID mutation guard

* Update and delete by stored ID.
* Names may be used for discovery only.
* Never delete every object matching a prefix without first comparing IDs to build state.

### Source-hash guard

Before mutation:

```text
assert sha256(design.md) == build_state.source_hash
```

When the hash changes, rerun source compilation and produce a change plan.

### Reversibility guard

Before a destructive migration:

* Export affected board or page.
* Record affected IDs.
* Write a rollback list.
* Do not combine deletion and replacement into the same unvalidated batch.

### No-detach guard

Instances may be overridden for text and sample data. They may not be detached to achieve a visual result.

### No-hardcode guard

Hardcoded visual values are blocking unless explicitly allowlisted.

Allowlist examples:

* Temporary chart coordinates
* Sample text content
* State indicator circles
* Scrim containment geometry
* Documentation-only labels and guides

Hardcoded colors are never allowed in managed components.

---

## 13. Automated Validation

## 13.1 Source validation

Blocking checks:

* YAML parses.
* Every `{token.reference}` resolves.
* Alias graph has no cycles.
* Token names are unique within their intended namespace.
* Color values parse.
* Dimensions use supported units.
* Typography entries contain required properties.
* Every documented component has a catalog entry.
* Every component catalog source path exists.
* Every required state from the prose specification is represented.

## 13.2 Penpot graph validation

Blocking checks:

* Required pages exist exactly once.
* Main components exist exactly once.
* Every component ID in build state still exists.
* Components are on the intended page.
* Variant family members are on the same page.
* No unnamed generic layers exist.
* Component nesting depth is no greater than four unless allowlisted.
* Overview specimens reference main components.
* No overview component instance is detached.
* Scratch-page objects are not referenced by published components.

## 13.3 Token-binding validation

For every managed layer:

* Fill color is token-bound.
* Stroke color is token-bound.
* Stroke width is token-bound where supported.
* Radius is token-bound.
* Padding and gaps are token-bound.
* Typography is token-bound.
* Shadow is token-bound.
* Opacity is token-bound where semantic.
* No raw visual value exists outside the allowlist.

Some Penpot API versions may expose the resolved value without exposing the binding identity. The agent must classify that as `manual-required`, not falsely report a successful binding check.

## 13.4 Design-policy validation

Blocking rules:

```text
radius == 2px
except role in [state-dot, chart-end-dot]

shadow allowed only for:
modal
popover
tooltip
toast
dropdown-menu
pinned-measure-tooltip

default control height == 36px
compact control height == 28px
period preset height == 32px
navigation item height == 40px
table header height == 34px
default table row height == 42px

font family == Inter
body text size >= 13px
critical financial text size >= 14px
numeric columns align right
labels align left
```

Additional checks:

* No gradients except an allowlisted sparkline area treatment.
* No decorative pill radius.
* No circular interactive control.
* Semantic states contain text or icon support.
* Historical state uses historical tokens.
* Destructive state uses error tokens.
* Primary emphasis is not applied to multiple competing actions in the same specimen.

OpenType `tnum` and `zero` should be validated when exposed by Penpot. If unavailable, add a visible component annotation and a manual-review issue.

## 13.5 Contrast validation

Calculate WCAG contrast from token values for every prescribed foreground/background pair:

```text
on-primary / primary
on-primary-container / primary-container
on-secondary / secondary
on-accent / accent
on-surface / background
on-surface-muted / background
positive / positive-container
warning / warning-container
error / error-container
info / info-container
historical / historical-container
```

Fail normal text below `4.5:1` and large text below `3:1`.

Also inspect actual component pairings so an otherwise valid token is not used against the wrong background.

## 13.6 Variant validation

For each component:

* Variant axes exactly match the catalog.
* Every required combination exists.
* No disallowed combination exists.
* Variant property spelling and capitalization are consistent.
* Shared layers preserve name, type, and hierarchy.
* Boolean properties use `true/false`.
* Instance text overrides survive representative variant switching.

## 13.7 Overview validation

* All ten sections exist in the specified order.
* Each required component family appears at least once.
* Major states appear in the appropriate section.
* All examples use instances.
* Section spacing is token-derived.
* The board uses the warm background token.
* Content remains inside the documented column.
* No modal specimen obscures the overall page.
* Section labels, dividers, and numbering are consistent.

## 13.8 Visual regression

During initial bootstrap:

* Compare structure and visual hierarchy against the supplied screenshot.
* Do not gate on pixel equality because the screenshot is scaled and compressed.

After human approval:

* Export the same boards at the same scale.
* Compare dimensions and object geometry first.
* Compare raster output second.
* Fail on missing sections, major positional shifts, changed token colors, or component disappearance.
* Require explicit baseline approval for intended visual changes.

---

## 14. Validation Report Contract

Every iteration should produce:

```json
{
  "sourceHash": "sha256:...",
  "penpotFileId": "...",
  "pageId": "...",
  "phase": "components.controls",
  "status": "failed",
  "summary": {
    "blocking": 2,
    "warnings": 1,
    "manualReview": 1
  },
  "issues": [
    {
      "rule": "DS-TOKEN-001",
      "severity": "blocking",
      "objectId": "...",
      "component": "control/button",
      "message": "Background fill is not bound to component.button.primary.background",
      "expected": "{component.button.primary.background}",
      "actual": "#34483B"
    }
  ]
}
```

A phase may be marked complete only when:

```text
blocking == 0
warnings are fixed or explicitly allowlisted
manual-review items are recorded
snapshot export succeeded
build-state.json was updated
```

---

## 15. Core Validation Rule Set

```json
{
  "rules": {
    "DS-SOURCE-001": "All source references resolve",
    "DS-SOURCE-002": "Source hash matches build state",
    "DS-PAGE-001": "Current file and page match the intended target",
    "DS-PAGE-002": "Managed pages exist exactly once",
    "DS-NAME-001": "No generic generated layer names",
    "DS-TOKEN-001": "No hardcoded color values",
    "DS-TOKEN-002": "Spacing and dimensions use approved tokens",
    "DS-TOKEN-003": "Typography uses approved tokens",
    "DS-RADIUS-001": "Radius is 2px except approved indicator dots",
    "DS-SHADOW-001": "Shadows appear only on approved elevated roles",
    "DS-COMP-001": "Canonical component exists exactly once",
    "DS-COMP-002": "Overview examples are component instances",
    "DS-COMP-003": "No detached instances",
    "DS-VARIANT-001": "Required variant combinations exist",
    "DS-VARIANT-002": "Variant layers remain structurally connected",
    "DS-A11Y-001": "Foreground/background contrast passes",
    "DS-A11Y-002": "Semantic color is accompanied by text or icon",
    "DS-TYPE-001": "Body and financial text meet minimum sizes",
    "DS-LAYOUT-001": "Component nesting depth does not exceed four",
    "DS-OVERVIEW-001": "Overview sections are complete and ordered",
    "DS-OVERVIEW-002": "Every catalog family has a visible specimen"
  }
}
```

---

## 16. Standard Agent Iteration Loop

For every iteration, the agent must perform this sequence:

```text
1. READ
   Read design.md, manifests, build state, and last validation report.

2. INSPECT
   Verify Penpot file, focused page, existing IDs, and current component state.

3. PLAN
   Select one bounded component family or overview section.
   Describe intended additions, updates, and deletions.

4. DRY RUN
   Resolve all target IDs and calculate expected postconditions.
   Make no writes.

5. APPLY
   Perform the smallest useful mutation batch.

6. VALIDATE
   Run source, structural, token, policy, variant, and accessibility checks.

7. EXPORT
   Export the changed board or specimen for visual inspection.

8. REPAIR OR ROLLBACK
   Repair exact failed objects.
   Roll back when the batch cannot be made valid without expanding scope.

9. RECORD
   Update build state, validation report, and snapshot metadata.

10. STOP
   Do not begin the next component family in the same iteration.
```

This follows Penpot’s own guidance to begin with inspection, describe changes before applying them, work in small reversible steps, and iterate through analysis, proposal, implementation, and review rather than attempting a one-shot design transformation. ([Penpot Help Center][1])

---

## 17. Initial Implementation Sequence

The first agent run should stop after:

1. Inspecting MCP capabilities.
2. Inventorying the target Penpot file.
3. Generating the five machine-readable planning artifacts.
4. Creating the six pages.
5. Importing or creating the three token sets.
6. Building the Foundations board.
7. Running the first complete validation report.

It should not start building components until the token system and Foundations board pass validation.

[1]: https://help.penpot.app/mcp/ "Penpot MCP server"
[2]: https://help.penpot.app/user-guide/design-systems/design-tokens/ "Design Tokens"
[3]: https://help.penpot.app/mcp/design-file-structure-best-practices/ "Design file structure and best practices"
[4]: https://help.penpot.app/user-guide/design-systems/variants/ "Variants"

