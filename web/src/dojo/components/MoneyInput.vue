<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { formatMoneyMinor, parseMoneyInput } from "../lib/money";

const props = defineProps<{ modelValue: number | null; label?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: number | null] }>();

const rawValue = ref(
  props.modelValue === null ? "" : formatMoneyMinor(props.modelValue),
);

watch(
  () => props.modelValue,
  (value) => {
    rawValue.value = value === null ? "" : formatMoneyMinor(value);
  },
);

const parsed = computed(() => parseMoneyInput(rawValue.value));

function handleInput(event: Event): void {
  rawValue.value = (event.target as HTMLInputElement).value;
  emit("update:modelValue", parseMoneyInput(rawValue.value));
}
</script>

<template>
  <label class="field">
    <span v-if="label">{{ label }}</span>
    <input
      :value="rawValue"
      inputmode="decimal"
      type="text"
      @input="handleInput"
    />
    <small v-if="rawValue && parsed === null"
      >Enter a signed dollar amount.</small
    >
  </label>
</template>

<style scoped>
.field {
  display: grid;
  gap: 0.25rem;
}

small {
  color: var(--dojo-brown-warning);
}
</style>
