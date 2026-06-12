<script setup lang="ts">
import type { Account } from "../types";

defineProps<{
  modelValue: string;
  accounts: Account[];
}>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="field">
    <span>Account</span>
    <select :value="modelValue" @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
      <option value="">Select account</option>
      <option v-for="account in accounts" :key="account.account_id" :value="account.account_id">
        {{ account.name }}
      </option>
    </select>
  </label>
</template>
