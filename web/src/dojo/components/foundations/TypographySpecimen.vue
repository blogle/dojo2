<script setup lang="ts">
interface TypographyRow {
  token: string;
  label: string;
  specs?: string;
  sample: string;
}

const props = defineProps<{
  rows: TypographyRow[];
}>();

const rootStyles = getComputedStyle(document.documentElement);

const tokenValue = (token: string, field: string) =>
  rootStyles.getPropertyValue(`--text-${token}-${field}`).trim();

const styleFor = (token: string) => ({
  fontFamily: `var(--text-${token}-font-family)`,
  fontSize: `var(--text-${token}-font-size)`,
  fontWeight: `var(--text-${token}-font-weight)`,
  lineHeight: `var(--text-${token}-line-height)`,
  letterSpacing: `var(--text-${token}-letter-spacing, normal)`,
  fontFeatureSettings: `var(--text-${token}-font-feature, normal)`,
});

const detailsFor = (row: TypographyRow) =>
  row.specs ??
  `${tokenValue(row.token, "font-size")} / ${tokenValue(row.token, "font-weight")} / ${tokenValue(row.token, "line-height")}`;

const mutedTokens = new Set(["body-lg", "body-md", "body-sm", "caption", "numeric"]);

const sampleClassFor = (token: string) =>
  mutedTokens.has(token)
    ? "type-row__sample type-row__sample--muted"
    : "type-row__sample";
</script>

<template>
  <div class="type-specimen" data-cy="typography-specimen-root">
    <article v-for="row in props.rows" :key="row.token" class="type-row">
      <div class="type-row__meta">
        <p class="type-row__token">{{ row.label }}</p>
        <p class="type-row__details">{{ detailsFor(row) }}</p>
      </div>
      <div class="type-row__sample-wrap">
        <p v-if="row.token === 'display-lg'" class="type-row__eyebrow">Typography</p>
        <p :class="sampleClassFor(row.token)" :style="styleFor(row.token)">
          {{ row.sample }}
        </p>
      </div>
    </article>
  </div>
</template>

<style scoped>
.type-specimen {
  display: grid;
  gap: 2px;
}

.type-row {
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr);
  gap: var(--space-sm);
  align-items: start;
}

.type-row__meta {
  display: grid;
  gap: 1px;
}

.type-row__token,
.type-row__details,
.type-row__eyebrow,
.type-row__sample {
  margin: 0;
}

.type-row__token,
.type-row__details,
.type-row__eyebrow {
  color: var(--color-on-surface-muted);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}

.type-row__sample-wrap {
  display: grid;
  gap: 2px;
}

.type-row__sample {
  color: var(--color-on-surface);
}

.type-row__sample--muted {
  color: var(--color-on-surface-muted);
}

@media (max-width: 640px) {
  .type-row {
    grid-template-columns: 1fr;
  }
}
</style>
