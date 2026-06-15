---
version: alpha
name: Dojo Grounded Ledger
description: A calm, compact, earth-toned design system for a high-density personal finance application. Warm mineral backgrounds, muted forest greens, restrained clay accents, and compact controls. Built for reading, comparing, entering, and reconciling dense financial information.

colors:
  primary: "#34483B"
  primary-hover: "#293A30"
  primary-active: "#1E2B22"
  on-primary: "#FFFFFF"
  primary-container: "#DCE7DD"
  on-primary-container: "#243229"
  secondary: "#66756A"
  on-secondary: "#FFFFFF"
  accent: "#9A5F43"
  on-accent: "#FFFFFF"
  background: "#F4F1E9"
  surface: "#FCFBF7"
  surface-raised: "#FFFFFF"
  surface-muted: "#ECE8DE"
  surface-selected: "#E3EADF"
  on-surface: "#202923"
  on-surface-muted: "#616B64"
  outline: "#CFC9BC"
  outline-strong: "#A9A294"
  positive: "#3F6B50"
  positive-container: "#DDEADE"
  warning: "#835C25"
  warning-container: "#F2E4C8"
  error: "#934B42"
  error-container: "#F3DCD8"
  info: "#4E6C70"
  info-container: "#DCE9E9"
  historical: "#735F44"
  historical-container: "#E9E0D2"
  scrim: "rgba(31, 38, 33, 0.42)"

typography:
  display-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.018em
  headline-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 19px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.35
  body-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  body-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.45
  body-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.4
  label-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.25
  label-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.25
  label-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: 0.01em
  caption:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 11px
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: 0.01em
  metric-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em
    fontFeature: '"tnum" 1, "zero" 1'
  metric-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.2
    fontFeature: '"tnum" 1, "zero" 1'
  numeric:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.35
    fontFeature: '"tnum" 1, "zero" 1'

rounded:
  all: 2px

spacing:
  micro: 2px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 32px
  3xl: 48px
  page-inline: 24px
  page-block: 20px
  section-gap: 24px
  control-gap: 8px
  row-height-compact: 36px
  row-height-default: 42px
  nav-collapsed: 56px
  nav-expanded: 208px

shadows:
  popover: "0 1px 2px rgba(32, 41, 35, 0.08)"
  modal: "0 12px 32px rgba(32, 41, 35, 0.16)"

transitions:
  fast: 120ms
  normal: 160ms
  slow: 200ms
  ease-out: "cubic-bezier(0.4, 0, 0.2, 1)"

components:
  app-shell:
    backgroundColor: "{colors.background}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
  navigation-rail:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface-muted}"
    borderRight: "1px solid {colors.outline}"
    width: "{spacing.nav-collapsed}"
    padding: "{spacing.sm}"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface-muted}"
    typography: "{typography.label-md}"
    rounded: "{rounded.all}"
    height: "40px"
    padding: "0 10px"
    iconWidth: "20px"
    iconHeight: "20px"
    hoverBackground: "{colors.surface-muted}"
    hoverTextColor: "{colors.on-surface}"
  nav-item-selected:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    rounded: "{rounded.all}"
    height: "40px"
    padding: "0 10px"
  nav-item-badge:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    fontSize: "11px"
    fontWeight: 600
    rounded: "{rounded.all}"
    padding: "1px 6px"
    minWidth: "18px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.all}"
    height: "36px"
    padding: "0 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-primary-disabled:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    opacity: 0.5
    cursor: not-allowed
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.all}"
    height: "36px"
    padding: "0 14px"
    border: "1px solid {colors.outline}"
  button-secondary-hover:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-surface}"
  button-tertiary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.all}"
    height: "28px"
    padding: "0 10px"
  button-tertiary-hover:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
  button-sm:
    height: "28px"
    padding: "0 10px"
    typography: "{typography.label-sm}"
  input-field:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.all}"
    height: "36px"
    padding: "0 10px"
    border: "1px solid {colors.outline}"
  input-field-focus:
    outline: "2px solid {colors.primary}"
    outlineOffset: "-1px"
  select-field:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.all}"
    height: "36px"
    padding: "0 10px"
    border: "1px solid {colors.outline}"
  page-header:
    backgroundColor: "{colors.background}"
    textColor: "{colors.on-surface}"
    borderBottom: "1px solid {colors.outline}"
    padding: "0 0 {spacing.lg}"
    margin: "0 0 {spacing.lg}"
  page-header-title:
    typography: "{typography.headline-lg}"
    textColor: "{colors.on-surface}"
  page-header-subtitle:
    typography: "{typography.body-md}"
    textColor: "{colors.on-surface-muted}"
  page-header-eyebrow:
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
    letterSpacing: 0.01em
    textTransform: uppercase
  page-header-sticky:
    backgroundColor: "{colors.background}"
    position: sticky
    top: 0
    zIndex: 10
  metric-strip:
    gap: "{spacing.xl}"
    padding: "{spacing.lg} 0"
  metric-item:
    label: "{typography.label-sm}"
    labelColor: "{colors.on-surface-muted}"
    value: "{typography.metric-lg}"
    valueColor: "{colors.on-surface}"
    auxColor: "{colors.on-surface-muted}"
    gap: "2px"
    minWidth: "140px"
  metric-item-delta-positive:
    textColor: "{colors.positive}"
    fontWeight: 600
  metric-item-delta-negative:
    textColor: "{colors.error}"
    fontWeight: 600
  metric-item-loading-skeleton:
    backgroundColor: "{colors.surface-muted}"
    rounded: "{rounded.all}"
    height: "28px"
    width: "80%"
  filter-bar:
    gap: "{spacing.control-gap}"
    padding: "{spacing.sm} 0"
  filter-chip:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.all}"
    height: "28px"
    padding: "0 8px"
  filter-chip-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
  period-selector:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  period-selector-preset:
    height: "32px"
    padding: "0 12px"
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
  period-selector-preset-hover:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-surface}"
  period-selector-preset-active:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    fontWeight: 600
  attention-panel:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  attention-panel-header:
    padding: "12px 16px"
  attention-panel-title:
    typography: "{typography.headline-sm}"
    textColor: "{colors.on-surface}"
  attention-panel-count:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-surface-muted}"
    fontSize: "12px"
    fontWeight: 600
    rounded: "{rounded.all}"
  attention-group-header:
    backgroundColor: "{colors.surface-muted}"
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
    padding: "8px 16px"
  attention-item:
    padding: "10px 16px"
    borderBottom: "1px solid {colors.outline}"
  attention-item-hover:
    backgroundColor: "{colors.surface-selected}"
  attention-item-dot-positive:
    backgroundColor: "{colors.positive}"
    size: "8px"
    rounded: "50%"
  attention-item-dot-warning:
    backgroundColor: "{colors.warning}"
    size: "8px"
    rounded: "50%"
  attention-item-dot-error:
    backgroundColor: "{colors.error}"
    size: "8px"
    rounded: "50%"
  attention-item-dot-info:
    backgroundColor: "{colors.info}"
    size: "8px"
    rounded: "50%"
  stacked-entity-card:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
    padding: "{spacing.lg}"
    gap: "6px"
  stacked-entity-card-hover:
    backgroundColor: "{colors.surface-selected}"
  stacked-entity-card-name:
    typography: "{typography.label-md}"
    textColor: "{colors.on-surface}"
  stacked-entity-card-value:
    fontWeight: 600
    textColor: "{colors.on-surface}"
  stacked-entity-card-delta-positive:
    textColor: "{colors.positive}"
    fontWeight: 600
  stacked-entity-card-delta-negative:
    textColor: "{colors.error}"
    fontWeight: 600
  stacked-entity-card-metadata:
    typography: "{typography.body-sm}"
    textColor: "{colors.on-surface-muted}"
  stacked-entity-card-icon:
    width: "18px"
    height: "18px"
    textColor: "{colors.secondary}"
  state-badge:
    rounded: "{rounded.all}"
    whiteSpace: nowrap
    gap: "4px"
  state-badge-sm:
    padding: "2px 8px"
    typography: "{typography.label-sm}"
  state-badge-md:
    padding: "3px 10px"
    typography: "{typography.label-md}"
  state-badge-positive:
    backgroundColor: "{colors.positive-container}"
    textColor: "{colors.positive}"
  state-badge-warning:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
  state-badge-error:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
  state-badge-info:
    backgroundColor: "{colors.info-container}"
    textColor: "{colors.info}"
  state-badge-historical:
    backgroundColor: "{colors.historical-container}"
    textColor: "{colors.historical}"
  sparkline:
    strokeWidth: "1.5"
    strokeLinecap: round
    strokeLinejoin: round
    areaFillOpacity: "0.15"
    endDotRadius: "2"
  sparkline-positive:
    strokeColor: "{colors.positive}"
  sparkline-negative:
    strokeColor: "{colors.error}"
  sparkline-neutral:
    strokeColor: "{colors.secondary}"
  trend-chart:
    backgroundColor: "transparent"
    seriesStrokeWidth: "1.5"
    seriesFillOpacity: "0.06"
    gridStroke: "{colors.outline}"
    gridStrokeWidth: "0.5"
    crosshairStroke: "{colors.outline-strong}"
    crosshairStrokeWidth: "1"
    crosshairDasharray: "3"
  trend-chart-empty:
    border: "1px dashed {colors.outline}"
    rounded: "{rounded.all}"
    textColor: "{colors.on-surface-muted}"
    typography: "{typography.body-sm}"
  trend-chart-tooltip:
    backgroundColor: "{colors.surface-raised}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
    padding: "8px 12px"
    shadow: "{shadows.popover}"
  trend-chart-measure-tooltip:
    backgroundColor: "{colors.surface-raised}"
    border: "1px solid {colors.outline-strong}"
    rounded: "{rounded.all}"
    padding: "10px 14px"
    shadow: "{shadows.popover}"
  trend-chart-measure-tooltip-pinned:
    borderColor: "{colors.primary}"
    shadow: "{shadows.modal}"
  trend-chart-series-colors:
    - "{colors.primary}"
    - "{colors.secondary}"
    - "{colors.accent}"
    - "{colors.info}"
    - "{colors.warning}"
  table-header:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-surface-muted}"
    typography: "{typography.label-sm}"
    height: "34px"
    padding: "0 12px"
  table-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    height: "{spacing.row-height-default}"
    padding: "0 12px"
  table-row-hover:
    backgroundColor: "{colors.surface-selected}"
  table-row-selected:
    backgroundColor: "{colors.surface-selected}"
  table-row-edited:
    borderLeft: "1px solid {colors.primary}"
  table-row-drag-handle:
    textColor: "{colors.on-surface-muted}"
    cursor: grab
  table-skeleton:
    backgroundColor: "{colors.surface-muted}"
    rounded: "{rounded.all}"
    animation: "pulse 1.5s ease-in-out infinite"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.all}"
    padding: "16px"
    border: "1px solid {colors.outline}"
  card-hover:
    backgroundColor: "{colors.surface-selected}"
  surface:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  surface-raised-variant:
    backgroundColor: "{colors.surface-raised}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  surface-muted-variant:
    backgroundColor: "{colors.surface-muted}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  divider:
    backgroundColor: "{colors.outline}"
    size: "1px"
  divider-strong:
    backgroundColor: "{colors.outline-strong}"
    size: "1px"
  modal:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.all}"
    padding: "0"
    border: "1px solid {colors.outline}"
    shadow: "{shadows.modal}"
  modal-header:
    padding: "{spacing.lg} {spacing.xl}"
    borderBottom: "1px solid {colors.outline}"
  modal-title:
    typography: "{typography.headline-sm}"
    textColor: "{colors.on-surface}"
  modal-body:
    padding: "{spacing.xl}"
  modal-footer:
    padding: "{spacing.lg} {spacing.xl}"
    borderTop: "1px solid {colors.outline}"
    display: flex
    justifyContent: flex-end
    gap: "{spacing.control-gap}"
  modal-scrim:
    backgroundColor: "{colors.scrim}"
  modal-large:
    maxWidth: "900px"
    maxHeight: "80vh"
  modal-form:
    maxWidth: "480px"
  modal-confirm:
    maxWidth: "400px"
  wizard:
    sidebarWidth: "200px"
    sidebarBackground: "{colors.surface-muted}"
  tooltip:
    backgroundColor: "{colors.on-surface}"
    textColor: "{colors.surface}"
    typography: "{typography.caption}"
    rounded: "{rounded.all}"
    padding: "6px 8px"
  toast:
    typography: "{typography.body-sm}"
    rounded: "{rounded.all}"
    padding: "10px 12px"
    shadow: "{shadows.popover}"
    maxWidth: "380px"
  toast-info:
    backgroundColor: "{colors.on-surface}"
    textColor: "{colors.surface}"
  toast-positive:
    backgroundColor: "{colors.positive}"
    textColor: "{colors.on-primary}"
  toast-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.on-primary}"
  toast-error:
    backgroundColor: "{colors.error}"
    textColor: "{colors.on-primary}"
  toast-undo:
    typography: "{typography.label-sm}"
    fontWeight: 600
    textDecoration: underline
    textUnderlineOffset: 2px
  toast-container:
    position: fixed
    bottom: "{spacing.xl}"
    right: "{spacing.xl}"
    zIndex: 2000
    display: flex
    flexDirection: column
    gap: "{spacing.sm}"
  persistent-warning-banner:
    padding: "10px 14px"
    rounded: "{rounded.all}"
    typography: "{typography.body-sm}"
    gap: "{spacing.md}"
  persistent-warning-banner-info:
    backgroundColor: "{colors.info-container}"
    textColor: "{colors.info}"
  persistent-warning-banner-warning:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
  persistent-warning-banner-error:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
  persistent-warning-banner-btn:
    height: "28px"
    padding: "0 12px"
    rounded: "{rounded.all}"
    typography: "{typography.label-sm}"
    fontWeight: 600
  persistent-warning-banner-btn-primary:
    backgroundColor: "currentColor"
    textColor: "{colors.surface-raised}"
  persistent-warning-banner-btn-secondary:
    backgroundColor: "transparent"
    textColor: "currentColor"
    border: "1px solid currentColor"
  historical-banner:
    backgroundColor: "{colors.historical-container}"
    textColor: "{colors.historical}"
    typography: "{typography.label-md}"
    rounded: "{rounded.all}"
    padding: "8px 12px"
  historical-banner-exit:
    height: "28px"
    padding: "0 12px"
    backgroundColor: "{colors.historical}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.all}"
    typography: "{typography.label-sm}"
    fontWeight: 600
  page-header-section-divider:
    backgroundColor: "{colors.outline}"
    size: "1px"
    margin: "{spacing.lg} 0"
  section-label:
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
    letterSpacing: 0.01em
    textTransform: uppercase
  derived-value-box:
    backgroundColor: "{colors.surface-selected}"
    border: "1px solid {colors.primary-container}"
    rounded: "{rounded.all}"
    padding: "{spacing.md}"
  move-preview-box:
    backgroundColor: "{colors.surface-selected}"
    border: "1px solid {colors.primary-container}"
    rounded: "{rounded.all}"
    padding: "{spacing.md}"
  move-preview-item:
    backgroundColor: "{colors.surface-raised}"
    rounded: "{rounded.all}"
    padding: "{spacing.sm}"
  validation-message:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    rounded: "{rounded.all}"
    padding: "{spacing.sm} {spacing.md}"
    typography: "{typography.body-sm}"
  error-message:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    rounded: "{rounded.all}"
    padding: "{spacing.sm} {spacing.md}"
    typography: "{typography.body-sm}"
  funding-dropdown-trigger:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    borderLeft: "1px solid rgba(255, 255, 255, 0.2)"
    rounded: "0 {rounded.all} {rounded.all} 0"
    width: "32px"
    height: "36px"
  funding-dropdown-menu:
    backgroundColor: "{colors.surface-raised}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
    shadow: "{shadows.popover}"
    minWidth: "200px"
    zIndex: 100
  funding-dropdown-item:
    padding: "8px 12px"
    typography: "{typography.body-md}"
    textColor: "{colors.on-surface}"
  funding-dropdown-item-hover:
    backgroundColor: "{colors.surface-selected}"
  funding-dropdown-item-disabled:
    opacity: 0.4
    cursor: not-allowed
  funding-dropdown-item-value:
    fontWeight: 600
    textColor: "{colors.on-surface-muted}"
  diff-view:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
  diff-view-panel-header:
    backgroundColor: "{colors.surface-muted}"
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
    padding: "8px 12px"
  diff-view-panel-body:
    padding: "{spacing.md}"
    typography: "{typography.body-sm}"
  diff-view-line-added:
    backgroundColor: "{colors.positive-container}"
  diff-view-line-removed:
    backgroundColor: "{colors.error-container}"
  diff-view-field-changed:
    backgroundColor: "{colors.surface-selected}"
  diff-view-field-before:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    textDecoration: line-through
  diff-view-field-after:
    backgroundColor: "{colors.positive-container}"
    textColor: "{colors.positive}"
  version-history-dot:
    width: "8px"
    height: "8px"
    rounded: "50%"
    backgroundColor: "{colors.secondary}"
  version-history-dot-selected:
    backgroundColor: "{colors.primary}"
  version-history-line:
    width: "1px"
    backgroundColor: "{colors.outline}"
  version-history-entry-hover:
    backgroundColor: "{colors.surface-selected}"
  version-history-entry-selected:
    backgroundColor: "{colors.surface-selected}"
  version-history-title:
    typography: "{typography.label-md}"
  version-history-meta:
    typography: "{typography.caption}"
    textColor: "{colors.on-surface-muted}"
  reconciliation-summary-label:
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
  reconciliation-summary-value:
    fontWeight: 600
    typography: "{typography.metric-md}"
  reconciliation-filter-btn:
    height: "28px"
    padding: "0 10px"
    typography: "{typography.label-sm}"
    textColor: "{colors.on-surface-muted}"
    rounded: "{rounded.all}"
  reconciliation-filter-btn-active:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    fontWeight: 600
  reconciliation-item:
    padding: "10px {spacing.xl}"
    borderBottom: "1px solid {colors.outline}"
  reconciliation-item-hover:
    backgroundColor: "{colors.surface-selected}"
  reconciliation-item-conflict:
    backgroundColor: "{colors.error-container}"
  reconciliation-item-toggle:
    width: "24px"
    height: "24px"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface-muted}"
  reconciliation-item-toggle-included:
    backgroundColor: "{colors.primary}"
    borderColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
  reconciliation-source-value:
    textColor: "{colors.error}"
    textDecoration: line-through
  reconciliation-proposed-value:
    fontWeight: 600
    textColor: "{colors.positive}"
  retired-modal:
    maxWidth: "600px"
    maxHeight: "80vh"
    backgroundColor: "{colors.surface-raised}"
    border: "1px solid {colors.outline}"
    rounded: "{rounded.all}"
    shadow: "{shadows.modal}"
  retired-modal-header:
    padding: "{spacing.lg} {spacing.xl}"
    borderBottom: "1px solid {colors.outline}"
  retired-modal-title:
    typography: "{typography.headline-sm}"
  retired-modal-search:
    padding: "{spacing.md} {spacing.xl}"
  retired-modal-item:
    padding: "10px {spacing.xl}"
    borderBottom: "1px solid {colors.outline}"
  retired-modal-item-title:
    typography: "{typography.label-md}"
  retired-modal-item-meta:
    typography: "{typography.caption}"
    textColor: "{colors.on-surface-muted}"
  retired-modal-batch:
    padding: "{spacing.lg} {spacing.xl}"
    borderTop: "1px solid {colors.outline}"
  skeleton-pulse:
    keyframes: |
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
---

# Dojo Design System

## 1. Visual Theme & Atmosphere

Dojo is a **grounded financial instrument**, not a lifestyle dashboard. The interface uses warm mineral backgrounds (`#F4F1E9`), muted forest greens (`#34483B`), restrained clay accents (`#9A5F43`), and crisp Inter typography on a compact 36–42px control rhythm. The design philosophy is "data-forward — containers recede": every surface, border, and control exists to organize financial information without competing with it. Pure white is reserved for raised surfaces; the page canvas is warm stone rather than clinical white.

The interface feels **quiet, exact, and durable**. Financial values are the strongest visual element. Containers use thin `outline` borders for separation rather than shadows or heavy fills. The single 2px corner radius is used universally — no pill shapes, no variable radii, no decorative rounding. Motion is functional and rare: navigation expansion, modal entry, disclosure toggles, and data-update highlights only.

**Key Characteristics:**
- Warm stone canvas (`background: #F4F1E9`) reduces glare; white (`surface-raised`) is for overlays only
- Forest green primary (`#34483B`) — the only action color; used for primary buttons, active nav, focused emphasis
- Uniform 2px corner radius on every component — no pill shapes, no variable radii
- Compact 36px default control height; 42px default row height; 32px compact variant
- Inter exclusively — no decorative display faces, no serif
- 1px outline borders for component separation; shadows only for modals and popovers
- Tabular numerals (`tnum`, `zero`) on every financial value, percentage, and date column
- Flat depth — tonal separation and borders over shadows

## 2. Color Palette & Roles

### Brand & Action

| Token | Hex | Role |
|---|---|---|
| `{colors.primary}` | `#34483B` | Main action color. Primary buttons, active navigation, focused emphasis, chart series |
| `{colors.primary-hover}` | `#293A30` | Primary button hover |
| `{colors.primary-active}` | `#1E2B22` | Primary button active/pressed |
| `{colors.on-primary}` | `#FFFFFF` | Text and icons on primary fills |
| `{colors.primary-container}` | `#DCE7DD` | Pale forest container for selected nav items, filter chips, active states |
| `{colors.on-primary-container}` | `#243229` | Text on primary-container fills |

### Secondary & Accent

| Token | Hex | Role |
|---|---|---|
| `{colors.secondary}` | `#66756A` | Supporting green for secondary controls, inactive icons, metadata, chart series |
| `{colors.on-secondary}` | `#FFFFFF` | Text on secondary fills |
| `{colors.accent}` | `#9A5F43` | Restrained clay accent for selected comparisons and deliberate highlights |
| `{colors.on-accent}` | `#FFFFFF` | Text on accent fills |

### Surfaces

| Token | Hex | Role |
|---|---|---|
| `{colors.background}` | `#F4F1E9` | Page canvas — warm stone, reduces glare |
| `{colors.surface}` | `#FCFBF7` | Default working surface — tables, panels, cards, controls |
| `{colors.surface-raised}` | `#FFFFFF` | White for overlays, modals, active editors, inputs |
| `{colors.surface-muted}` | `#ECE8DE` | Table headers, section headers, subtle surface separation |
| `{colors.surface-selected}` | `#E3EADF` | Hover/selected row treatment, derived value backgrounds |

### Text

| Token | Hex | Role |
|---|---|---|
| `{colors.on-surface}` | `#202923` | Primary text, high-value numeric data. Avoid pure black |
| `{colors.on-surface-muted}` | `#616B64` | Secondary labels, helper text, timestamps, metadata |

### Borders

| Token | Hex | Role |
|---|---|---|
| `{colors.outline}` | `#CFC9BC` | 1px borders on cards, tables, inputs, dividers |
| `{colors.outline-strong}` | `#A9A294` | Stronger borders, chart crosshairs, emphasized dividers |

### Semantic

| Token | Hex | Role |
|---|---|---|
| `{colors.positive}` | `#3F6B50` | Favorable change, funded state, successful completion |
| `{colors.positive-container}` | `#DDEADE` | Positive state badges, success backgrounds |
| `{colors.warning}` | `#835C25` | Due soon, underfunded, stale, attention-needed |
| `{colors.warning-container}` | `#F2E4C8` | Warning badges, validation messages, warning banners |
| `{colors.error}` | `#934B42` | Overspending, invalid input, destructive confirmation |
| `{colors.error-container}` | `#F3DCD8` | Error badges, error messages, diff removed lines |
| `{colors.info}` | `#4E6C70` | Neutral notices, reconciliation context |
| `{colors.info-container}` | `#DCE9E9` | Info badges, info banners |
| `{colors.historical}` | `#735F44` | Sepia-brown for global as-of mode, historical context |
| `{colors.historical-container}` | `#E9E0D2` | Historical banners, historical context backgrounds |

### Scrim

| Token | Hex | Role |
|---|---|---|
| `{colors.scrim}` | `rgba(31, 38, 33, 0.42)` | Modal backdrop overlay. Never blur the application behind overlays |

### Usage Rules
- Never rely on hue alone. Pair semantic color with an icon, concise label, or text.
- Semantic state badges must use the paired container + text token (e.g., `positive-container` with `positive` text).
- Multiple simultaneous states must remain independently readable rather than collapsing into one row background.
- Charts use a restrained sequence: forest, sage, clay, blue-green, ochre. Grid lines use `outline` at low emphasis.
- Avoid rainbow palettes, gradients, neon colors, and large translucent washes.

## 3. Typography

### Font Family

**Inter** is the sole typeface — used for every display, headline, body, label, caption, metric, and numeric role. Inter provides a neutral, highly legible voice with consistent rhythm across prose, controls, tables, and metrics. System sans-serif fallbacks: `ui-sans-serif, system-ui, sans-serif`. Do not introduce a decorative display face.

### Hierarchy

| Token | Size | Weight | Line Ht | Letter Spacing | Tabular | Use |
|---|---|---|---|---|---|---|
| `{typography.display-lg}` | 32px | 700 | 1.15 | -0.025em | no | Page titles, metric display values |
| `{typography.headline-lg}` | 24px | 700 | 1.2 | -0.018em | no | Page headers |
| `{typography.headline-md}` | 19px | 600 | 1.3 | -0.01em | no | Section titles, metric strip values |
| `{typography.headline-sm}` | 16px | 600 | 1.35 | — | no | Panel/modal titles, card titles |
| `{typography.body-lg}` | 16px | 400 | 1.5 | — | no | Lead paragraphs |
| `{typography.body-md}` | 14px | 400 | 1.45 | — | no | Default body, table cells |
| `{typography.body-sm}` | 13px | 400 | 1.4 | — | no | Dense tables, helper text, metadata |
| `{typography.label-lg}` | 14px | 600 | 1.25 | — | no | Strong labels |
| `{typography.label-md}` | 13px | 600 | 1.25 | — | no | Button labels, controls, nav items |
| `{typography.label-sm}` | 12px | 600 | 1.25 | 0.01em | no | Column headers, state indicators, section labels |
| `{typography.caption}` | 11px | 500 | 1.35 | 0.01em | no | Fine print, timestamps, tooltips |
| `{typography.metric-lg}` | 28px | 700 | 1.1 | -0.02em | `tnum, zero` | Large financial values |
| `{typography.metric-md}` | 18px | 600 | 1.2 | — | `tnum, zero` | Summary values, prominent table totals |
| `{typography.numeric}` | 14px | 500 | 1.35 | — | `tnum, zero` | Amounts, percentages, dates in aligned columns |

### Usage Rules
- Page titles use `headline-lg`; section titles use `headline-md`; panel and modal titles use `headline-sm`.
- Body copy defaults to `body-md`. Use `body-sm` for dense tables and metadata only when legibility remains strong.
- Controls use `label-md`. Small state indicators and column headings use `label-sm`.
- Large financial values use `metric-lg`; summary values use `metric-md`.
- All amounts, percentages, dates in aligned columns, and comparison-heavy values use `numeric` or metric styles with `tnum` and `zero` font features.
- Sentence case is the default. Avoid all-caps labels except for established abbreviations. Bold is reserved for hierarchy and important values, not general emphasis.
- Minimum body text: 13px (`body-sm`). Critical financial data: minimum 14px (`body-md` or `numeric`).
- Amounts align to the right in tables. Labels align to the left. Preserve minus signs, currency symbols, and decimal precision.

## 4. Layout

### Spacing Scale
| Token | Value | Use |
|---|---|---|
| `{spacing.micro}` | 2px | Tight gaps between icon and label, badge padding |
| `{spacing.xs}` | 4px | Rail item gaps, icon-to-text spacing |
| `{spacing.sm}` | 8px | Control groups, button padding, search padding |
| `{spacing.md}` | 12px | Panel padding, field spacing, card internal gaps |
| `{spacing.lg}` | 16px | Card padding, section grouping |
| `{spacing.xl}` | 24px | Page inline padding, modal padding, section gaps |
| `{spacing.2xl}` | 32px | Large gaps, summary groupings |
| `{spacing.3xl}` | 48px | Major section separators, empty states |
| `{spacing.page-inline}` | 24px | Left/right page padding |
| `{spacing.page-block}` | 20px | Top/bottom page padding |
| `{spacing.section-gap}` | 24px | Vertical gap between major sections |
| `{spacing.control-gap}` | 8px | Gap between adjacent controls and buttons |

### Row/Control Heights
| Token | Value | Use |
|---|---|---|
| `{spacing.row-height-compact}` | 36px | Compact table rows, control height |
| `{spacing.row-height-default}` | 42px | Standard table rows |
| `{spacing.nav-collapsed}` | 56px | Collapsed navigation rail width |
| `{spacing.nav-expanded}` | 208px | Expanded navigation rail width |

### Page Structure
1. Application shell with compact utility region
2. Page header with title, metadata, and primary actions
3. Optional metric strip or persistent status banner
4. Main working surface: table, ledger, chart, or detail content
5. Contextual actions adjacent to the object they affect

Breakpoint behavior: On screens 1280px and wider, minimum spacing between peer elements must not be less than `lg` (16px). On narrow screens (< 640px), page headers stack vertically.

## 5. Elevation & Depth

Depth is conveyed primarily through tonal separation, borders, and placement. The application should feel nearly flat.

| Level | Treatment | Use |
|---|---|---|
| Level 0 — Canvas | `{colors.background}` | Page background, deepest layer |
| Level 1 — Surface | `{colors.surface}` + 1px `{colors.outline}` border | Tables, panels, cards, nav rail |
| Level 2 — Muted | `{colors.surface-muted}` + 1px `{colors.outline}` border | Table headers, section headers, attention group headers |
| Level 3 — Raised | `{colors.surface-raised}` + 1px `{colors.outline}` border | Modals, popovers, active editors, inputs, menus |
| Level 4 — Popover | Level 3 + `{shadows.popover}` | Dropdown menus, tooltips, date pickers |
| Level 5 — Modal | Level 3 + `{shadows.modal}` + `{colors.scrim}` | Large detail modals, confirmation dialogs |

**Shadow tokens:**
- `{shadows.popover}`: `0 1px 2px rgba(32, 41, 35, 0.08)` — menus, tooltips, dropdowns
- `{shadows.modal}`: `0 12px 32px rgba(32, 41, 35, 0.16)` — modals, dialogs

**Rules:** Shadows are subtle and infrequent. Tables and ordinary cards do not need shadows. Hover changes tone or border contrast by a small amount — no elevation change on hover. Use scrims only for modal focus. Do not blur the application behind overlays.

## 6. Shapes

### Border Radius
The system exposes a **single 2px radius** (`{rounded.all}`) for every component. No exceptions.

**Why a single radius:** A uniform corner radius avoids visual noise, keeps the interface crisp, and eliminates the need to choose between variants. Every component — buttons, inputs, navigation items, menus, cards, modals, panels, state indicators, table containers, tooltips, overlays — uses `2px`.

**What NOT to use:** Pill shapes (9999px), circular controls (50%), variable radii per component.

### Icons
- Simple outlined style with consistent 1.75–2px strokes
- Square optical bounds
- Minimal internal detail
- Filled icons reserved for selected or strongly emphasized states
- Avoid oversized icons, illustrated empty states, mascots, and ornamental financial imagery

## 7. Transition Tokens

| Token | Duration | Curve | Use |
|---|---|---|---|
| `{transitions.fast}` | 120ms | ease-out | Hover, focus, color transitions |
| `{transitions.normal}` | 160ms | ease-out | Navigation expansion, disclosure, dropdown |
| `{transitions.slow}` | 200ms | ease-out | Modal entry, overlay show/hide |
| `{ease-out}` | — | `cubic-bezier(0.4, 0, 0.2, 1)` | Global easing curve |

**Rules:** Data updates should preserve position and briefly tint the changed value or row for no more than 800ms. Do not animate every number from zero. Respect `prefers-reduced-motion` by removing translation and width interpolation where needed while retaining immediate state changes. Avoid spring physics, bounce, parallax, continuous animation, celebratory effects, and animated gradients.

## 8. Components

### 8.1 Application Shell & Layout

#### `app-shell`
The top-level application chrome. Uses flex layout with `min-height: 100vh`.

| Prop | Type | Default | Description |
|---|---|---|---|
| `showOverlay` | boolean | false | Shows scrim overlay for modals and drawers |

**Slots:** `navigation` (left rail), `topbar` (top bar), `default` (main content), `overlay` (teleported overlay region)

**States:** Default, overlay-visible (applies `{colors.scrim}` via `modal-scrim` component class).

#### `stack`
Vertical flex container. Props: `gap` (default `{spacing.lg}`), `tag` (default `'div'`).

#### `inline`
Horizontal flex container. Props: `gap`, `wrap`, `align`.

#### `grid`
CSS Grid container. Props: `columns`, `gap`.

#### `surface`
Container with background and border. Variants: `raised` (`surface-raised`), `paper` (`surface`), `muted` (`surface-muted`), `transparent`. Props: `variant`, `padding`, `radius`, `border`.

#### `divider`
Horizontal or vertical `<hr>` element. Props: `orientation` (horizontal/vertical), `size` (default 1px), `color` (default `outline`), `spacing`.

**States:** Default, strong (uses `{colors.outline-strong}`).

---

### 8.2 Navigation

#### `navigation-rail`
Collapsible sidebar navigation with primary and secondary item groups, expand/collapse toggle, and optional persistence.

| Prop | Type | Default | Description |
|---|---|---|---|
| `modelValue` | string | `''` | Currently selected item key |
| `primaryItems` | NavItem[] | required | Primary navigation items |
| `secondaryItems` | NavItem[] | `[]` | Utility/secondary nav items |
| `expanded` | boolean\|null | `null` | Controlled expansion state (null = internal) |
| `collapsible` | boolean | `true` | Show collapse toggle |
| `collapsedWidth` | string | `var(--dojo-nav-collapsed)` | Width when collapsed |
| `expandedWidth` | string | `var(--dojo-nav-expanded)` | Width when expanded |

**Interface `NavItem`:** `key` (string), `label` (string), `icon` (SVG string), `badge?` (string|number)

**States:**
- **Collapsed** — 56px wide, icons only, labels hidden
- **Expanded** — 208px wide, icons + labels visible
- **Default item** — `transparent` background, `{colors.on-surface-muted}` text
- **Hover item** — `{colors.surface-muted}` background, `{colors.on-surface}` text
- **Selected item** — `{colors.primary-container}` background, `{colors.on-primary-container}` text
- **Badge** — `{colors.primary}` background, `{colors.on-primary}` text, 11px font

**Layout:**
- Background: `{colors.surface}`
- Border-right: `1px solid {colors.outline}`
- Padding: `{spacing.sm}`
- Item height: 40px, icon: 20×20px
- Transition: width `{transitions.normal}` ease-out
- Animation does not trigger on pointer hover — only explicit toggle

---

### 8.3 Page Data Components

#### `page-header`
Page-level header with title, subtitle, eyebrow, metadata, actions, and tabs.

| Prop | Type | Default | Description |
|---|---|---|---|
| `title` | string | `''` | Page title in `{typography.headline-lg}` |
| `subtitle` | string | — | Optional subtitle in `{typography.body-md}` muted |
| `eyebrow` | string | — | Optional eyebrow label in `{typography.label-sm}` uppercase |
| `metadata` | string | — | Optional metadata line |
| `primaryActions` | boolean | false | Shows action slot region |
| `sticky` | boolean | false | Sticks to top of viewport on scroll |

**Slots:** `eyebrow`, `title`, `subtitle`, `actions`, `metadata`, `tabs`, `default`

**States:** Default, sticky (position: sticky, top: 0, z-index: 10, `{colors.background}` fill). Responsive: actions stack vertically below 640px.

#### `metric-strip`
Horizontal row of metrics with values, deltas, status badges, and loading state.

| Prop | Type | Default | Description |
|---|---|---|---|
| `items` | MetricItem[] | required | Array of metric items |
| `scrollable` | boolean | false | Enables horizontal scroll |

**Interface `MetricItem`:** `key` (string), `label` (string), `value` (string), `auxValue?` (string), `delta?` (number), `icon?` (string), `loading?` (boolean), `status?` (StatusVariant), `clickable?` (boolean)

**States:**
- **Default** — label in `{typography.label-sm}` uppercase muted, value in `{typography.metric-lg}`
- **Loading** — skeleton placeholder (28px tall, 80% width, pulse animation)
- **Delta positive** — `{colors.positive}` text
- **Delta negative** — `{colors.error}` text
- **Delta neutral** — `{colors.on-surface-muted}` text
- **Status** — renders `state-badge` with severity variant
- **Scrollable** — overflow-x auto with touch scrolling

#### `filter-bar`
Search input + active filter chips + advanced filters region + sort + clear actions.

| Prop | Type | Default | Description |
|---|---|---|---|
| `searchValue` | string | `''` | Search input value (v-model) |
| `showSearch` | boolean | `true` | Show search input |
| `activeFilters` | FilterChip[] | `[]` | Active filter chips |
| `hasActiveFilters` | boolean | `false` | Show "Clear all" button |

**Interface `FilterChip`:** `key` (string), `label` (string), `value` (string)

**Slots:** `search`, `filters`, `actions`, `sort`, `advanced`

**States:** Default, advanced (toggle visible), active filter chips, clear-all visible when filters present.

**Filter chip:** 28px height, `{colors.primary-container}` background, `{colors.on-primary-container}` text. Hover: `{colors.primary}` background, `{colors.on-primary}` text.

#### `period-selector`
Preset period buttons with optional custom range and comparison toggle.

| Prop | Type | Default | Description |
|---|---|---|---|
| `modelValue` | string | `''` | Active preset key |
| `presets` | PeriodPreset[] | 1M/3M/6M/YTD/1Y/All | Preset options |
| `comparison` | boolean | `false` | Show comparison toggle |

**Interface `PeriodPreset`:** `key` (string), `label` (string)

**States:** Default preset (muted text), active preset (`{colors.primary-container}` background, 600 weight), comparison toggle.

#### `attention-panel`
Collapsible panel grouping items by severity (error/warning/info/positive).

| Prop | Type | Default | Description |
|---|---|---|---|
| `title` | string | `'Attention'` | Panel title |
| `items` | AttentionItem[] | `[]` | Array of attention items |

**Interface `AttentionItem`:** `key` (string), `title` (string), `summary?` (string), `severity` (StatusVariant), `timestamp?` (string), `metadata?` (string), `primaryAction?` (string), `secondaryAction?` (string)

**States:** Collapsed/expanded, grouped by severity, empty state, severity dot colors (8px circle, colored by severity).

#### `stacked-entity-card`
Entity card with name, value, delta, metadata, status badge, sparkline trend, and actions.

| Prop | Type | Default | Description |
|---|---|---|---|
| `name` | string | required | Entity name |
| `primaryValue` | string | required | Primary value |
| `icon` | string | — | SVG icon |
| `delta` | number | — | Change value |
| `metadata` | string | — | Secondary info |
| `status` | StatusVariant | — | Status badge variant |
| `trend` | number[] | — | Sparkline data |
| `clickable` | boolean | — | Makes entire card clickable |

**States:** Default, clickable (cursor pointer), hover (`{colors.surface-selected}`), delta positive/negative coloring.

---

### 8.4 Display Components

#### `state-badge`
Semantic status badge with 5 severity variants and 2 sizes.

| Prop | Type | Default | Description |
|---|---|---|---|
| `variant` | StatusVariant | `'info'` | Severity variant |
| `size` | `'sm' \| 'md'` | `'sm'` | Badge size |

**StatusVariant type:** `'positive' | 'warning' | 'error' | 'info' | 'historical'`

**States:** 5 color variants (each uses its container + text token pair), 2 sizes (sm: 2px 8px at 12px font, md: 3px 10px at 13px font).

#### `sparkline`
Mini inline SVG chart with line, area fill, and end dot.

| Prop | Type | Default | Description |
|---|---|---|---|
| `data` | number[] | required | Data points |
| `width` | number | 80 | SVG width |
| `height` | number | 24 | SVG height |
| `positive` | boolean | — | Use positive green |
| `negative` | boolean | — | Use error red |
| `area` | boolean | false | Show area fill gradient |
| `showEndDot` | boolean | false | Show end circle |
| `color` | string | — | Custom stroke color override |

**States:** Positive (green stroke), negative (red stroke), neutral (`{colors.secondary}`), area fill gradient (15% to 1% opacity), end dot.

#### `trend-chart`
Full SVG line chart with multiple series, hover crosshair, data tooltip, and measurement mode with drag-to-select interval analysis.

| Prop | Type | Default | Description |
|---|---|---|---|
| `data` | TrendSeries[] | required | Series data |
| `width` | number | 600 | SVG width |
| `height` | number | 240 | Chart height |
| `measurement` | boolean | false | Enable drag-to-measure |
| `formatX` | function | — | X-axis label formatter |
| `formatY` | function | — | Y-axis label formatter |

**Interface `TrendSeries`:** `label` (string), `data` ({x: number, y: number}[]), `color?` (string)

**States:**
- **Empty** — dashed border placeholder, "No data available" text
- **Default** — grid lines, series paths, area fills, x-axis labels
- **Hover** — vertical crosshair (dashed, `{colors.outline-strong}`), floating data tooltip
- **Measurement (drag)** — tinted selection band, floating interval measure tooltip with start/end/delta/%/duration
- **Measurement (hover on selected)** — tooltip reappears
- **Measurement (pinned)** — tooltip persists on click, `{colors.primary}` border, dismisses on Escape or outside click

**Series colors:** `[{colors.primary}, {colors.secondary}, {colors.accent}, {colors.info}, {colors.warning}]`

---

### 8.5 Table Components

#### `hierarchical-category-table`
Table with expandable group rows, sorting, drag-and-drop reordering, and slot-based cell rendering.

| Prop | Type | Default | Description |
|---|---|---|---|
| `columns` | Column[] | required | Column definitions |
| `rows` | HierarchicalRow[] | required | Row data |
| `expandable` | boolean | false | Allow group row expansion |
| `stickyHeader` | boolean | false | Sticky header row |
| `selectedKeys` | string[] | — | Selected row keys |
| `reorderable` | boolean | false | Enable drag reorder |
| `sortKey` | string | — | Current sort column |
| `sortDir` | 'asc'\|'desc' | — | Sort direction |

**Interface `Column`:** `key`, `label`, `align?`, `width?`, `sortable?`

**Interface `HierarchicalRow`:** `key`, `label`, `depth?`, `children?`, `group?`, `expanded?`, cells per column, `selected?`

**States:**
- **Header** — `{colors.surface-muted}`, `{typography.label-sm}`, 34px height, sticky when enabled
- **Row default** — `{colors.surface}`, `{typography.body-md}`, 42px height
- **Row hover** — `{colors.surface-selected}`
- **Row selected** — `{colors.surface-selected}`
- **Group row** — stronger weight, muted fill, disclosure controls
- **Drag handle** — grab cursor, muted color
- **Reorder mode** — persistent mode bar, drag targets with outline

#### `virtualized-transaction-ledger`
Virtualized table with sticky headers, inline editing, infinite scroll, and skeleton loading states.

| Prop | Type | Default | Description |
|---|---|---|---|
| `columns` | LedgerColumn[] | required | Column definitions |
| `rows` | LedgerRow[] | required | Row data |
| `stickyHeader` | boolean | false | Sticky header |
| `selectedKeys` | string[] | — | Selected row keys |
| `editedKeys` | string[] | — | Rows with pending edits |
| `editingKey` | string | — | Currently editing row key |
| `editableCols` | string[] | — | Editable column keys |
| `loading` | boolean | false | Loading state |
| `hasMore` | boolean | false | More data available |
| `overscan` | number | — | Virtual scroll overscan |

**States:** Loading (skeleton rows), empty (no data message), editing (inline input replaces cell), edited (pending marker), scroll loading (infinite scroll trigger), selected.

---

### 8.6 Modal Components

#### `large-detail-modal`
Large full-featured modal (max 900px). Teleported to body.

| Prop | Type | Default | Description |
|---|---|---|---|
| `visible` | boolean | required | Show/hide |
| `title` | string | — | Modal title |
| `subtitle` | string | — | Modal subtitle |
| `sticky` | boolean | false | Sticky header |

**Slots:** `title`, `subtitle`, `tabs`, `default`, `footer`/`actions`

**States:** Open (scrim visible, modal animated in with opacity + translateY 200ms), closed.

#### `form-modal`
Compact form modal (max 480px).

| Prop | Type | Default | Description |
|---|---|---|---|
| `visible` | boolean | required | Show/hide |
| `title` | string | — | Modal title |
| `submitText` | string | `'Save'` | Submit button text |
| `cancelText` | string | `'Cancel'` | Cancel button text |
| `dangerText` | string | — | Destructive action text |
| `submitDisabled` | boolean | false | Disable submit |
| `loading` | boolean | false | Loading state |

**States:** Default, loading (button disabled + spinner), danger variant.

#### `confirmation-dialog`
Compact confirmation dialog (max 400px).

| Prop | Type | Default | Description |
|---|---|---|---|
| `visible` | boolean | required | Show/hide |
| `title` | string | — | Dialog title |
| `body` | string | — | Description/consequence |
| `confirmText` | string | `'Confirm'` | Confirm button text |
| `cancelText` | string | `'Cancel'` | Cancel button text |
| `variant` | `'neutral'\|'warning'\|'destructive'` | `'neutral'` | Dialog variant |
| `icon` | string | — | Optional icon SVG |
| `consequence` | string | — | Named consequence |

**States:** Neutral, warning, destructive (error styling on confirm button).

#### `entity-wizard`
Multi-step wizard with sidebar progress.

| Prop | Type | Default | Description |
|---|---|---|---|
| `visible` | boolean | required | Show/hide |
| `steps` | WizardStep[] | required | Step definitions |
| `currentStep` | number | 0 | Active step index |
| `saving` | boolean | false | Saving state |
| `error` | string | — | Error message |
| `showSidePanel` | boolean | false | Show side panel slot |

**Interface `WizardStep`:** `key`, `label`, `description?`, `completed?`

**States:** Active step, completed step, upcoming step, saving (submit disabled), error.

---

### 8.7 Feedback Components

#### `undo-toast`
Toast notification system with 4 semantic variants, undo action, hover-to-pause, auto-dismiss.

**Exposed methods via `defineExpose`:** `addToast(toast)`, `removeToast(id)`, `toasts`

**Interface `Omit<ToastItem, 'id' | '_timer'>`:**
- `message` (string) — Toast text
- `variant?` (`'info' | 'positive' | 'warning' | 'error'`) — defaults to `'info'`
- `undoAction?` (function) — Undo callback
- `undoLabel?` (string) — defaults to `'Undo'`
- `timeout?` (number) — defaults to `4000ms`

**States:**
- **Info** — `{colors.on-surface}` background, `{colors.surface}` text
- **Positive** — `{colors.positive}` background, `{colors.on-primary}` text
- **Warning** — `{colors.warning}` background, `{colors.on-primary}` text
- **Error** — `{colors.error}` background, `{colors.on-primary}` text
- **Hover** — timer pauses
- **Enter** — slide in from right (translateX 20px → 0, 160ms)
- **Leave** — slide out to right (0 → translateX 20px, 120ms)

#### `persistent-warning-banner`
Banner at top of content area with severity variant, icon, and action buttons.

| Prop | Type | Default | Description |
|---|---|---|---|
| `severity` | `'info'\|'warning'\|'error'` | `'info'` | Severity variant |
| `title` | string | — | Banner title |
| `description` | string | — | Banner description |
| `primaryAction` | string | — | Primary CTA label |
| `secondaryAction` | string | — | Secondary CTA label |
| `dismissible` | boolean | false | Show dismiss button |

**States:** Info (info-container), warning (warning-container), error (error-container), dismissible.

#### `historical-banner`
Sepia-toned banner for global historical data viewing mode.

| Prop | Type | Default | Description |
|---|---|---|---|
| `label` | string | `'Viewing historical data'` | Banner label |
| `description` | string | — | Description text |
| `exitLabel` | string | `'Return to current'` | Exit button text |

**State:** `{colors.historical-container}` background, `{colors.historical}` text and exit button.

---

### 8.8 Specialized Components

#### `funding-dropdown`
Split-button: primary action + dropdown menu with amount-labeled items.

| Prop | Type | Default | Description |
|---|---|---|---|
| `primaryLabel` | string | `'Fund'` | Primary action label |
| `actions` | FundingAction[] | `[]` | Dropdown menu actions |

**Interface `FundingAction`:** `key` (string), `label` (string), `value?` (string), `disabled?` (boolean), `disabledReason?` (string)

**States:** Default, item hover, disabled item (40% opacity, not-allowed cursor), dropdown open/close (fade + translateY 4px, 120ms).

**Layout:** Primary button `{colors.primary}` + dropdown trigger `{colors.primary}` with 32px width + dropdown menu `{colors.surface-raised}` with 1px outline and popover shadow.

#### `goal-editor`
Goal strategy selector (target/limit/savings-rate) with field slot, derived value display, and validation.

| Prop | Type | Default | Description |
|---|---|---|---|
| `modelValue` | GoalState | required | Current goal state |
| `modes` | GoalMode[] | Target/Limit/Savings rate | Strategy options |
| `derivedValue` | string\|null | `null` | Projected value |
| `validation` | string | — | Validation message |

**States:** Default, mode selected (active button: `{colors.primary-container}`), derived value shown (tinted box), validation shown (warning-container background).

#### `move-funds-editor`
Source/destination selector with amount input and live balance preview.

| Prop | Type | Default | Description |
|---|---|---|---|
| `modelValue` | MoveState | required | Form state |
| `sources` | MoveSource[] | `[]` | Source accounts |
| `destinations` | MoveSource[] | `[]` | Destination accounts |
| `error` | string | — | Error message |

**States:** Default, error (error-container message), can-submit (source + destination + amount > 0), live preview with computed balances.

---

### 8.9 History & Review Components

#### `diff-view`
Three layout modes: side-by-side, unified, and summary (field-by-field before/after).

| Prop | Type | Default | Description |
|---|---|---|---|
| `layout` | `'side-by-side'\|'unified'\|'summary'` | `'summary'` | Diff layout mode |
| `beforeLabel` | string | `'Before'` | Left/source panel label |
| `afterLabel` | string | `'After'` | Right/target panel label |
| `fields` | DiffField[] | `[]` | Field diff data (summary mode) |
| `unifiedLines` | UnifiedLine[] | `[]` | Unified diff lines |

**States:** Side-by-side (2-column grid), unified (monospace lines with +/- markers), summary (field-by-field before/after with added/removed/changed highlighting).

**Diff coloring:** Added = `{colors.positive-container}`, Removed = `{colors.error-container}`, Changed = `{colors.surface-selected}`.

#### `reconciliation-review`
Full reconciliation interface with summary totals, filter tabs, item toggles, conflict badges, and residual display.

| Prop | Type | Default | Description |
|---|---|---|---|
| `items` | ReconciliationItem[] | `[]` | Items to reconcile |
| `activeFilter` | string | `'All'` | Active filter tab |
| `sourceTotal` | string | `'$0.00'` | Source total |
| `currentTotal` | string | `'$0.00'` | Current total |
| `proposedTotal` | string | `'$0.00'` | Proposed total |
| `proposedDiff` | number | `0` | Difference from current |
| `residual` | string | `'$0.00'` | Remaining difference |

**States:** Filter tabs (All/Included/Excluded/Conflict), item included (checked), item excluded (unchecked), conflict (error-container background + badge), empty, residual display.

#### `version-history`
Timeline-styled version list with select, restore, and compare actions.

| Prop | Type | Default | Description |
|---|---|---|---|
| `versions` | VersionRecord[] | `[]` | Version entries |
| `selectedId` | string | — | Selected version ID |

**States:** Default, selected (highlighted background, primary dot), hover, empty, restorable version (shows Restore button).

#### `retired-items-modal`
Modal listing retired/deleted items with search, restore, batch restore, and view history.

| Prop | Type | Default | Description |
|---|---|---|---|
| `visible` | boolean | required | Show/hide |
| `title` | string | `'Retired Items'` | Modal title |
| `items` | RetiredItem[] | `[]` | Retired items |
| `search` | string | `''` | Search filter |
| `batchRestore` | boolean | false | Show batch restore |

**States:** Open (teleported with scrim), search focused, empty results, item with restore, batch restore visible (for multiple items).

---

### 8.10 Button Grammar Reference

The system uses three button levels, each with consistent height, padding, and typography:

| Level | Height | Padding | Typography | Background | Text | Border |
|---|---|---|---|---|---|---|
| **Primary** | 36px | 0 14px | `label-md` | `{colors.primary}` | `{colors.on-primary}` | none |
| **Secondary** | 36px | 0 14px | `label-md` | `{colors.surface}` | `{colors.on-surface}` | 1px `{colors.outline}` |
| **Tertiary** | 28px | 0 10px | `label-sm` | transparent | `{colors.primary}` | none |

Button states: default, hover, active/pressed, disabled, loading. Disabled primary: 0.5 opacity, not-allowed cursor.

**Compact variant** (btn--sm): 28px height, 0 10px padding, `label-sm` typography. Used in toolbars, table actions, and compact layouts.

---

### 8.11 Input & Form Controls

| Element | Height | Background | Border | Focus | Typography |
|---|---|---|---|---|---|
| Text input | 36px | `{colors.surface-raised}` | 1px `{colors.outline}` | 2px `{colors.primary}` outline, -1px offset | `{typography.body-md}` |
| Select | 36px | `{colors.surface-raised}` | 1px `{colors.outline}` | 2px `{colors.primary}` outline, -1px offset | `{typography.body-md}` |
| Currency input | 36px | `{colors.surface-raised}` (24px left padding for $ sign) | 1px `{colors.outline}` | 2px `{colors.primary}` outline | `{typography.body-md}` |

Placeholder: `{colors.on-surface-muted}` at 0.6 opacity. Labels: `{typography.label-sm}` uppercase above field.

---

### 8.12 Focus Management

Focus is expressed with a clear 2px `{colors.primary}` outline and 2px offset. Applied via `:focus-visible` globally. Focus treatment must remain visible on every surface and must not be removed in favor of hover styling.

Keyboard: Focus order follows visual order, Enter submits valid simple forms, Escape closes transient surfaces, destructive shortcuts require confirmation.

## 9. Do's and Don'ts

### Do
- Make financial values, state, and comparison the strongest visual elements
- Use the single 2px radius on every component without exception
- Apply `tnum` and `zero` font features to every financial value, percentage, and date column
- Use warm neutrals and restrained earth tones consistently
- Keep repeated actions close to the records they affect
- Support keyboard navigation, visible focus, compact density, and sensible defaults
- Use borders, spacing, typography, and local indicators before adding cards or shadows
- Keep canonical action labels unchanged: `Add`, `Cancel`, `Save`, `Fund`, `Move funds`, `Retire`, `Restore`, `Remove`, `Reconcile`, `Apply reconciliation`
- Display exact amounts in funding actions and previews
- Make historical mode persistently and semantically distinct
- Provide text and icon support for every color-coded state
- Use primary buttons sparingly — limit visual primary emphasis to the action that advances or commits the current task
- Use `{colors.primary-container}` / `{colors.primary}` pairing for selected states, filter chips, and active controls
- Preserve stable geometry, column alignment, and focus order
- Use page-header divider (1px `{colors.outline}`, `{spacing.lg}` margin) between header and content

### Don't
- Don't use saturated fintech blues, neon greens, glossy gradients, glass effects, or cryptocurrency-inspired styling
- Don't introduce a second corner radius — the entire system uses exactly 2px
- Don't use pill shapes (9999px) for any component
- Don't use circular controls (50% radius) — state indicator dots are the only circular element
- Don't wrap every number or section in an individual card
- Don't hide common actions behind hover-only affordances or generic overflow menus
- Don't require pointer interaction for common entry, editing, filtering, or navigation
- Don't animate routine data merely to create movement
- Don't rely on red versus green alone to communicate financial meaning
- Don't center numeric table columns or sacrifice alignment for visual symmetry
- Don't allow historical, pending, warning, or reconciliation states to become subtle enough to miss
- Don't use oversized hero typography, promotional illustrations, mascots, or decorative empty states in working views
- Don't add shadows to tables, cards, or controls — shadows are reserved for modals and popovers only
- Don't use weight 700 (display-lg, metric-lg) for body text — reserve it for large values and page titles only

## 10. Responsive Behavior

### Breakpoints

| Name | Width | Key Changes |
|---|---|---|
| Small | < 640px | Page header stacks vertically; actions fill width; navigation rail may become drawer |
| Medium | 640–1279px | Standard compact layout; reduced page padding |
| Large | ≥ 1280px | Full layout; minimum spacing between peer elements is `lg` (16px) |

### Collapsing Strategy
- Navigation rail: collapsed by default at all sizes; user can expand. On small screens, opens as explicit drawer overlay
- Page header: title + actions on same row at ≥ 640px; stacks vertically below
- Tables: horizontal scroll for irreducible tables; pinned identifying columns; collapse low-priority metadata
- Hero typography: stair-step down at small widths (display-lg 32px → 28px; headline-lg 24px → 20px)
- Metric strip: horizontal scroll at all sizes when content overflows

### Touch Targets
- Minimum 44 × 44px interactive area on mobile (WCAG AA)
- Controls maintain 36px visual height but hit area may be enlarged through padding

### Accessibility Requirements
- All text on colored backgrounds must satisfy WCAG AA contrast ratios (4.5:1 normal, 3:1 large)
- Semantic state badges use paired container + text tokens (guaranteed contrast)
- Icon-only controls must provide accessible names via `aria-label` or tooltip
- Every pointer interaction has a keyboard path
- Every semantic state has a non-color indicator (icon or label)
- Do not reduce body text below 13px or critical financial data below 14px

## 11. Agent Prompt Guide

### Quick Token Reference
- **Page canvas:** `{colors.background}` (#F4F1E9)
- **Surface:** `{colors.surface}` (#FCFBF7)
- **White surface:** `{colors.surface-raised}` (#FFFFFF)
- **Primary text:** `{colors.on-surface}` (#202923)
- **Muted text:** `{colors.on-surface-muted}` (#616B64)
- **Action color:** `{colors.primary}` (#34483B)
- **Border:** `{colors.outline}` (#CFC9BC)
- **Corner radius:** 2px everywhere
- **Control height:** 36px
- **Default spacing:** `{spacing.sm}` (8px) between controls, `{spacing.lg}` (16px) card padding
- **Font:** Inter at 14px/400/1.45 for body (`{typography.body-md}`)

### Example Component Prompts
- "Create a primary button: `{colors.primary}` background, `{colors.on-primary}` text, 36px height, 0 14px padding, 2px radius, Inter 13px/600."
- "Design a table header: `{colors.surface-muted}` background, `{colors.on-surface-muted}` text, 34px height, Inter 12px/600 uppercase, sticky when enabled."
- "Build a card: `{colors.surface}` background, 1px `{colors.outline}` border, 2px radius, 16px padding. No shadow. Hover tints to `{colors.surface-selected}`."
- "Create a text input: `{colors.surface-raised}` background, 1px `{colors.outline}` border, 2px radius, 36px height, 0 10px padding. Focus: 2px `{colors.primary}` outline."
- "Design a state badge: `{colors.positive-container}` background, `{colors.positive}` text (or warning/error/info/historical variant), 2px radius, 2px 8px padding, Inter 12px/600."
- "Build a toast: `{colors.on-surface}` background (info variant), `{colors.surface}` text, 2px radius, 10px 12px padding, popover shadow. Slides in from right 160ms."
