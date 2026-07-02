<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue?: string;
    label?: string;
    helper?: string;
    error?: string;
    disabled?: boolean;
    name?: string;
  }>(),
  {
    modelValue: undefined,
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
  <label class="field" data-cy="date-picker-root">
    <span v-if="label || $slots.label" class="field__label">
      <slot name="label">{{ label }}</slot>
    </span>

    <span class="field__control-shell">
      <span class="field__prefix" aria-hidden="true">📅</span>

      <input
        class="field__control field__control--with-prefix"
        :value="modelValue"
        :disabled="disabled"
        type="date"
        :name="name"
        @input="
          emit('update:modelValue', ($event.target as HTMLInputElement).value)
        "
      />
    </span>

    <span v-if="error" class="field__message field__message--error">{{
      error
    }}</span>
    <span
      v-else-if="helper || $slots.helper"
      class="field__message field__message--helper"
    >
      <slot name="helper">{{ helper }}</slot>
    </span>
  </label>
</template>

<style scoped>
.field {
  display: grid;
  gap: var(--space-xs);
}

.field__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.field__control-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.field__prefix {
  position: absolute;
  left: 10px;
  color: var(--color-on-surface-muted);
  pointer-events: none;
}

.field__control {
  width: 100%;
  min-height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.field__control--with-prefix {
  padding-left: 28px;
}

.field__control:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.field__message {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.field__message--helper {
  color: var(--color-on-surface-muted);
}

.field__message--error {
  color: var(--color-error);
}
</style>
