<script setup lang="ts">
export type StateBadgeVariant =
  | "positive"
  | "warning"
  | "error"
  | "info"
  | "historical"
  | "partial-funding";

withDefaults(
  defineProps<{
    variant?: StateBadgeVariant;
    size?: "sm" | "md";
    icon?: string;
  }>(),
  {
    variant: "info",
    size: "sm",
    icon: undefined,
  },
);
</script>

<template>
  <span
    :class="['state-badge', `state-badge--${variant}`, `state-badge--${size}`]"
    data-cy="state-badge-root"
  >
    <svg
      v-if="icon"
      class="state-badge__icon"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <circle v-if="icon === 'check'" cx="8" cy="8" r="6" fill="currentColor" opacity="0.15" />
      <path v-if="icon === 'check'" d="M5.5 8l2 2 3.5-3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      <circle v-if="icon === 'clock'" cx="8" cy="8" r="6" fill="currentColor" opacity="0.15" />
      <path v-if="icon === 'clock'" d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      <circle v-if="icon === 'alert'" cx="8" cy="8" r="6" fill="currentColor" opacity="0.15" />
      <path v-if="icon === 'alert'" d="M8 5v3M8 10.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    </svg>
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

.state-badge--partial-funding {
  background: var(--color-partial-funding-container);
  color: var(--color-partial-funding);
}

.state-badge__icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
</style>
