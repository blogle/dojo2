<script setup lang="ts">
import TextField from "./TextField.vue";

withDefaults(
  defineProps<{
    modelValue?: string;
    label?: string;
    placeholder?: string;
    helper?: string;
    error?: string;
    disabled?: boolean;
    name?: string;
  }>(),
  {
    modelValue: "",
    label: undefined,
    placeholder: "0.00",
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
  <TextField
    :model-value="modelValue"
    :label="label"
    :placeholder="placeholder"
    :helper="helper"
    :error="error"
    :disabled="disabled"
    :name="name"
    inputmode="decimal"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #prefix>$</template>
  </TextField>
</template>
