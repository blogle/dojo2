<script setup lang="ts">
interface TypographyRow {
  token: string;
  label: string;
  sample: string;
}

defineProps<{
  rows: TypographyRow[];
}>();

const rootStyles = getComputedStyle(document.documentElement);

const tokenValue = (token: string, field: string) =>
  rootStyles.getPropertyValue(`--text-${token}-${field}`).trim();
</script>

<template>
  <div class="type-specimen" data-cy="typography-specimen-root">
    <div class="type-specimen__hero">
      <p class="type-specimen__eyebrow">Typography</p>
      <h2 class="type-specimen__display">Display Large</h2>
      <p class="type-specimen__headline-lg">Headline Large</p>
      <p class="type-specimen__headline-md">Headline Medium</p>
      <p class="type-specimen__headline-sm">Headline Small</p>
      <p class="type-specimen__body-md">Body Large — The quick brown fox jumps over the lazy dog.</p>
      <p class="type-specimen__body-sm">Body Small — The quick brown fox jumps over the lazy dog.</p>
      <p class="type-specimen__label">Label Large</p>
      <p class="type-specimen__caption">Label Small</p>
      <p class="type-specimen__metric">$12,345.67</p>
      <p class="type-specimen__numeric">$1,234.56</p>
    </div>

    <div class="type-specimen__rows">
      <article v-for="row in rows" :key="row.token" class="type-row">
        <p class="type-row__meta">{{ row.label }}</p>
        <div class="type-row__content">
          <p
            class="type-row__sample"
            :style="{
              fontFamily: `var(--text-${row.token}-font-family)`,
              fontSize: `var(--text-${row.token}-font-size)`,
              fontWeight: `var(--text-${row.token}-font-weight)`,
              lineHeight: `var(--text-${row.token}-line-height)`,
              letterSpacing: `var(--text-${row.token}-letter-spacing, normal)`,
              fontFeatureSettings: `var(--text-${row.token}-font-feature, normal)`,
            }"
          >
            {{ row.sample }}
          </p>
          <p class="type-row__details">
            {{ tokenValue(row.token, "font-size") }} / {{ tokenValue(row.token, "font-weight") }} / {{ tokenValue(row.token, "line-height") }}
          </p>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.type-specimen {
  display: grid;
  gap: var(--space-xl);
}

.type-specimen__hero,
.type-specimen__rows {
  display: grid;
  gap: var(--space-xs);
}

.type-specimen__eyebrow,
.type-row__meta,
.type-row__details,
.type-specimen__caption {
  color: var(--color-on-surface-muted);
}

.type-specimen__eyebrow,
.type-row__meta {
  margin: 0;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  text-transform: uppercase;
}

.type-specimen__display,
.type-specimen__headline-lg,
.type-specimen__headline-md,
.type-specimen__headline-sm,
.type-specimen__body-md,
.type-specimen__body-sm,
.type-specimen__label,
.type-specimen__caption,
.type-specimen__metric,
.type-specimen__numeric,
.type-row__sample,
.type-row__details {
  margin: 0;
}

.type-specimen__display {
  font-family: var(--text-display-lg-font-family);
  font-size: var(--text-display-lg-font-size);
  font-weight: var(--text-display-lg-font-weight);
  line-height: var(--text-display-lg-line-height);
  letter-spacing: var(--text-display-lg-letter-spacing);
}

.type-specimen__headline-lg {
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
  letter-spacing: var(--text-headline-lg-letter-spacing);
}

.type-specimen__headline-md {
  font-family: var(--text-headline-md-font-family);
  font-size: var(--text-headline-md-font-size);
  font-weight: var(--text-headline-md-font-weight);
  line-height: var(--text-headline-md-line-height);
  letter-spacing: var(--text-headline-md-letter-spacing, 0);
}

.type-specimen__headline-sm {
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.type-specimen__body-md {
  font-family: var(--text-body-lg-font-family);
  font-size: var(--text-body-lg-font-size);
  font-weight: var(--text-body-lg-font-weight);
  line-height: var(--text-body-lg-line-height);
}

.type-specimen__body-sm {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.type-specimen__label {
  font-family: var(--text-label-lg-font-family);
  font-size: var(--text-label-lg-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-label-lg-line-height);
}

.type-specimen__caption {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing);
}

.type-specimen__metric {
  font-family: var(--text-metric-lg-font-family);
  font-size: var(--text-metric-lg-font-size);
  font-weight: var(--text-metric-lg-font-weight);
  line-height: var(--text-metric-lg-line-height);
  letter-spacing: var(--text-metric-lg-letter-spacing);
  font-feature-settings: var(--text-metric-lg-font-feature);
}

.type-specimen__numeric {
  font-family: var(--text-numeric-font-family);
  font-size: var(--text-numeric-font-size);
  font-weight: var(--text-numeric-font-weight);
  line-height: var(--text-numeric-line-height);
  font-feature-settings: var(--text-numeric-font-feature);
}

.type-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: var(--space-sm);
  align-items: baseline;
}

.type-row__details {
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}

@media (max-width: 640px) {
  .type-row {
    grid-template-columns: 1fr;
  }
}
</style>
