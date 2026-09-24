<script setup lang="ts">
import { computed } from "vue";

export interface BinaryToggleOption {
  value: string;
  label: string;
  icon?: string;
}

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: [BinaryToggleOption, BinaryToggleOption];
    label: string;
    kind: "status" | "direction";
    dataName: string;
    disabled?: boolean;
  }>(),
  { disabled: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const currentIndex = computed(() =>
  props.options[0].value === props.modelValue ? 0 : 1,
);
const currentOption = computed(() => props.options[currentIndex.value]);
const nextOption = computed(() => props.options[1 - currentIndex.value]);

function toggle() {
  emit("update:modelValue", nextOption.value.value);
}
</script>

<template>
  <div class="binary-toggle">
    <span class="binary-toggle__label">{{ label }}</span>
    <button
      type="button"
      class="binary-toggle__button"
      :class="[
        `binary-toggle__button--${kind}`,
        `binary-toggle__button--${currentOption.value.toLowerCase()}`,
      ]"
      :data-cy="`binary-toggle-${dataName}`"
      :aria-label="`${label} is ${currentOption.label}. Switch to ${nextOption.label}`"
      :disabled="disabled"
      @click="toggle"
    >
      <span v-if="currentOption.icon" aria-hidden="true">{{
        currentOption.icon
      }}</span>
      {{ currentOption.label }}
    </button>
  </div>
</template>

<style scoped>
.binary-toggle {
  display: grid;
  gap: var(--space-xs);
  min-width: 0;
}

.binary-toggle__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.binary-toggle__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  width: 100%;
  min-height: 36px;
  padding: 1px var(--space-sm);
  overflow: hidden;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
  color: var(--color-on-surface);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--transition-fast) var(--transition-ease-out),
    border-color var(--transition-fast) var(--transition-ease-out);
}

.binary-toggle__button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.binary-toggle__button:hover:enabled {
  background: var(--color-surface-muted);
}

.binary-toggle__button--cleared {
  border-color: var(--color-positive);
  color: var(--color-positive);
}

.binary-toggle__button--pending {
  border-color: var(--color-warning);
}

.binary-toggle__button--inflow {
  color: var(--color-positive);
}

.binary-toggle__button--outflow {
  color: var(--color-error);
}

.binary-toggle__button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
