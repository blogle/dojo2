<script setup lang="ts">
export interface RadioGroupOption {
  value: string;
  label: string;
}

withDefaults(
  defineProps<{
    modelValue: string;
    options: RadioGroupOption[];
    label?: string;
    name?: string;
    disabled?: boolean;
  }>(),
  {
    label: undefined,
    name: undefined,
    disabled: false,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <div class="radio-group" data-cy="radio-group-root">
    <span v-if="label" class="radio-group__label">{{ label }}</span>
    <div class="radio-group__options">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        :disabled="disabled"
        :class="[
          'radio-group__option',
          { 'radio-group__option--active': modelValue === option.value },
        ]"
        @click="emit('update:modelValue', option.value)"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.radio-group {
  display: grid;
  gap: var(--space-xs);
}

.radio-group__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.radio-group__options {
  display: flex;
  gap: var(--space-xs);
}

.radio-group__option {
  appearance: none;
  padding: 0 var(--space-md);
  min-height: 36px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
  cursor: pointer;
  transition:
    background-color var(--transition-fast) var(--transition-ease-out),
    border-color var(--transition-fast) var(--transition-ease-out);
}

.radio-group__option:hover:enabled {
  background: var(--color-surface-muted);
}

.radio-group__option--active {
  background: var(--color-primary-container);
  border-color: var(--color-primary);
  color: var(--color-on-primary-container);
}

.radio-group__option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
