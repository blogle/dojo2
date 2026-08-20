<script setup lang="ts">
import { computed, useId } from "vue";

withDefaults(
  defineProps<{
    modelValue?: string;
    options?: string[];
    label?: string;
    helper?: string;
    error?: string;
    disabled?: boolean;
    name?: string;
    placeholder?: string;
  }>(),
  {
    modelValue: "",
    options: () => [],
    label: "Institution",
    helper: undefined,
    error: undefined,
    disabled: false,
    name: undefined,
    placeholder: "Type or choose an institution",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const generatedId = useId();
const listId = computed(() => `institution-options-${generatedId}`);
</script>

<template>
  <label class="field" data-cy="institution-combobox-root">
    <span v-if="label" class="field__label">{{ label }}</span>
    <input
      class="field__control"
      type="text"
      :value="modelValue"
      :disabled="disabled"
      :name="name"
      :placeholder="placeholder"
      :list="listId"
      autocomplete="organization"
      @input="
        emit('update:modelValue', ($event.target as HTMLInputElement).value)
      "
    />
    <datalist :id="listId">
      <option v-for="option in options" :key="option" :value="option" />
    </datalist>
    <span v-if="error" class="field__message field__message--error">{{
      error
    }}</span>
    <span v-else-if="helper" class="field__message field__message--helper">{{
      helper
    }}</span>
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
