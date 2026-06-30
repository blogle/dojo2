<script setup lang="ts">
interface SpacingToken {
  label: string;
  token: string;
}

defineProps<{
  tokens: SpacingToken[];
}>();

const rootStyles = getComputedStyle(document.documentElement);
const tokenValue = (token: string) => rootStyles.getPropertyValue(token).trim();
</script>

<template>
  <div class="spacing-scale" data-cy="spacing-scale-root">
    <article v-for="entry in tokens" :key="entry.token" class="spacing-row">
      <p class="spacing-row__label">{{ entry.label }}</p>
      <div class="spacing-row__bar-wrap">
        <div class="spacing-row__bar" :style="{ width: `var(${entry.token})` }" />
      </div>
      <p class="spacing-row__value">{{ tokenValue(entry.token) }}</p>
    </article>
  </div>
</template>

<style scoped>
.spacing-scale {
  display: grid;
  gap: var(--space-xs);
}

.spacing-row {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr) 64px;
  gap: var(--space-sm);
  align-items: center;
}

.spacing-row__label,
.spacing-row__value {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
  font-weight: var(--text-caption-font-weight);
  line-height: var(--text-caption-line-height);
}

.spacing-row__bar-wrap {
  height: 10px;
  display: flex;
  align-items: center;
}

.spacing-row__bar {
  height: 8px;
  background: var(--color-primary);
}

@media (max-width: 640px) {
  .spacing-row {
    grid-template-columns: 72px minmax(0, 1fr) 56px;
  }
}
</style>
