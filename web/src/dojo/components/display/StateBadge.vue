<script setup lang="ts">
export type StateBadgeVariant =
  | "positive"
  | "warning"
  | "error"
  | "info"
  | "historical";

withDefaults(
  defineProps<{
    variant?: StateBadgeVariant;
    size?: "sm" | "md";
  }>(),
  {
    variant: "info",
    size: "sm",
  },
);
</script>

<template>
  <span
    :class="['state-badge', `state-badge--${variant}`, `state-badge--${size}`]"
    data-cy="state-badge-root"
  >
    <slot />
  </span>
</template>

<style scoped>
.state-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--radius-all);
  white-space: nowrap;
}

.state-badge--sm {
  padding: 2px 8px;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
}

.state-badge--md {
  padding: 3px 10px;
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.state-badge--positive {
  background: var(--color-positive-container);
  color: var(--color-positive);
}

.state-badge--warning {
  background: var(--color-warning-container);
  color: var(--color-warning);
}

.state-badge--error {
  background: var(--color-error-container);
  color: var(--color-error);
}

.state-badge--info {
  background: var(--color-info-container);
  color: var(--color-info);
}

.state-badge--historical {
  background: var(--color-historical-container);
  color: var(--color-historical);
}
</style>
