<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    value: number;
    variant?: "positive" | "warning" | "error" | "partial" | "neutral";
    label?: string;
    showValue?: boolean;
  }>(),
  {
    variant: "neutral",
    label: undefined,
    showValue: false,
  },
);

const clampedValue = computed(() => Math.min(100, Math.max(0, props.value)));
</script>

<template>
  <div class="progress-bar" data-cy="progress-bar-root">
    <div v-if="label || showValue" class="progress-bar__header">
      <span v-if="label" class="progress-bar__label">{{ label }}</span>
      <span v-if="showValue" class="progress-bar__value"
        >{{ clampedValue }}%</span
      >
    </div>
    <div class="progress-bar__track">
      <div
        class="progress-bar__fill"
        :class="`progress-bar__fill--${variant}`"
        :style="{ width: `${clampedValue}%` }"
      />
    </div>
  </div>
</template>

<style scoped>
.progress-bar {
  display: grid;
  gap: var(--space-xs);
}

.progress-bar__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-bar__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.progress-bar__value {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface);
}

.progress-bar__track {
  height: 8px;
  background: var(--color-surface-muted);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-normal) var(--transition-ease-out);
}

.progress-bar__fill--positive {
  background: var(--color-positive);
}

.progress-bar__fill--warning {
  background: var(--color-warning);
}

.progress-bar__fill--error {
  background: var(--color-error);
}

.progress-bar__fill--partial {
  background: var(--color-partial-funding);
}

.progress-bar__fill--neutral {
  background: var(--color-outline-strong);
}
</style>
