<script setup lang="ts">
interface Swatch {
  label: string;
  token: string;
}

interface SwatchGroup {
  name: string;
  swatches: Swatch[];
}

defineProps<{
  groups: SwatchGroup[];
}>();

const rootStyles = getComputedStyle(document.documentElement);

const tokenValue = (token: string) => rootStyles.getPropertyValue(token).trim();
</script>

<template>
  <div class="swatch-groups" data-cy="color-swatch-grid-root">
    <section v-for="group in groups" :key="group.name" class="swatch-group">
      <h3 class="swatch-group__title">{{ group.name }}</h3>
      <div class="swatch-grid">
        <article v-for="swatch in group.swatches" :key="swatch.token" class="swatch-card">
          <div class="swatch-card__chip" :style="{ backgroundColor: `var(${swatch.token})` }" />
          <div class="swatch-card__meta">
            <p class="swatch-card__label">{{ swatch.label }}</p>
            <p class="swatch-card__value">{{ tokenValue(swatch.token) }}</p>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.swatch-groups {
  display: grid;
  gap: var(--space-lg);
}

.swatch-group {
  display: grid;
  gap: var(--space-sm);
}

.swatch-group__title {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  text-transform: uppercase;
}

.swatch-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.swatch-card {
  display: grid;
  gap: var(--space-xs);
  width: 92px;
  align-content: start;
}

.swatch-card__chip {
  height: 48px;
  border: 1px solid var(--color-outline);
}

.swatch-card__meta {
  display: grid;
  gap: 2px;
}

.swatch-card__label,
.swatch-card__value {
  margin: 0;
}

.swatch-card__label {
  color: var(--color-on-surface);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}

.swatch-card__value {
  color: var(--color-on-surface-muted);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}
</style>
