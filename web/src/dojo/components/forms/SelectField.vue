<script setup lang="ts">
export interface SelectFieldOption {
  value: string;
  label: string;
  disabled?: boolean;
}

withDefaults(
  defineProps<{
    modelValue?: string;
    label?: string;
    helper?: string;
    error?: string;
    disabled?: boolean;
    name?: string;
    options: SelectFieldOption[];
  }>(),
  {
    modelValue: "",
    label: undefined,
    helper: undefined,
    error: undefined,
    disabled: false,
    name: undefined,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <label class="select-field" data-cy="select-field-root">
    <span v-if="label" class="select-field__label">{{ label }}</span>
    <span class="select-field__control-shell">
      <select
        class="select-field__control"
        :value="modelValue"
        :disabled="disabled"
        :name="name"
        @change="
          emit('update:modelValue', ($event.target as HTMLSelectElement).value)
        "
      >
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
      <span class="select-field__chevron" aria-hidden="true">▾</span>
    </span>
    <span
      v-if="error"
      class="select-field__message select-field__message--error"
      >{{ error }}</span
    >
    <span
      v-else-if="helper"
      class="select-field__message select-field__message--helper"
      >{{ helper }}</span
    >
  </label>
</template>

<style scoped>
.select-field {
  display: grid;
  gap: var(--space-xs);
}

.select-field__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.select-field__control-shell {
  position: relative;
}

.select-field__control {
  width: 100%;
  min-height: 36px;
  padding: 0 34px 0 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  appearance: none;
}

.select-field__control:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.select-field__chevron {
  position: absolute;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  color: var(--color-on-surface-muted);
  pointer-events: none;
}

.select-field__message {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.select-field__message--helper {
  color: var(--color-on-surface-muted);
}

.select-field__message--error {
  color: var(--color-error);
}
</style>
