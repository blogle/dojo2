<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "tertiary";
    size?: "default" | "sm";
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    loading?: boolean;
    block?: boolean;
  }>(),
  {
    variant: "primary",
    size: "default",
    type: "button",
    disabled: false,
    loading: false,
    block: false,
  },
);

const isDisabled = computed(() => props.disabled || props.loading);
</script>

<template>
  <button
    :type="type"
    :disabled="isDisabled"
    :class="[
      'button',
      `button--${variant}`,
      `button--${size}`,
      { 'button--block': block, 'button--loading': loading },
    ]"
    data-cy="button-root"
  >
    <span v-if="$slots.icon" class="button__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <span class="button__label"><slot /></span>
  </button>
</template>

<style scoped>
.button {
  appearance: none;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: var(--radius-all);
  transition:
    background-color var(--motion-fast) var(--motion-ease-out),
    color var(--motion-fast) var(--motion-ease-out),
    border-color var(--motion-fast) var(--motion-ease-out),
    opacity var(--motion-fast) var(--motion-ease-out);
  cursor: pointer;
}

.button--default {
  min-height: 36px;
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.button--sm {
  min-height: 28px;
  padding: 0 10px;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
}

.button--primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.button--primary:hover:enabled {
  background: var(--color-primary-hover);
}

.button--primary:active:enabled {
  background: var(--color-primary-active);
}

.button--secondary {
  border-color: var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface);
}

.button--secondary:hover:enabled {
  background: var(--color-surface-muted);
}

.button--tertiary {
  padding: 0 10px;
  border-color: transparent;
  background: transparent;
  color: var(--color-primary);
}

.button--tertiary:hover:enabled {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.button--block {
  width: 100%;
}

.button--loading,
.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button__icon {
  display: inline-flex;
}

.button__icon :deep(svg) {
  width: 16px;
  height: 16px;
}

.button__label {
  white-space: nowrap;
}
</style>
