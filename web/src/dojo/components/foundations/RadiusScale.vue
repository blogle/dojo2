<script setup lang="ts">
interface RadiusToken {
  label: string;
  token: string;
}

defineProps<{
  tokens: RadiusToken[];
}>();

const rootStyles = getComputedStyle(document.documentElement);
const tokenValue = (token: string) => rootStyles.getPropertyValue(token).trim();
</script>

<template>
  <div class="radius-scale" data-cy="radius-scale-root">
    <article v-for="entry in tokens" :key="entry.token" class="radius-card">
      <div class="radius-card__shape" :style="{ borderRadius: `var(${entry.token})` }" />
      <p class="radius-card__label">{{ entry.label }}</p>
      <p class="radius-card__value">{{ tokenValue(entry.token) }}</p>
    </article>
  </div>
</template>

<style scoped>
.radius-scale {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.radius-card {
  width: 74px;
  display: grid;
  gap: var(--space-xs);
  justify-items: center;
}

.radius-card__shape {
  width: 42px;
  height: 42px;
  border: 1px solid var(--color-outline);
  background: color-mix(in srgb, var(--color-surface) 72%, var(--color-primary-container));
}

.radius-card__label,
.radius-card__value {
  margin: 0;
  text-align: center;
}

.radius-card__label {
  color: var(--color-on-surface);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}

.radius-card__value {
  color: var(--color-on-surface-muted);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}
</style>
