<script setup lang="ts">
import { computed } from "vue";

import type { Category } from "../types";
import CategorySelect from "./CategorySelect.vue";

const props = defineProps<{
  categories: Category[];
  categoryId: string;
  systemCategory: string;
  useSystemCategory: boolean;
  showHidden?: boolean;
}>();

const emit = defineEmits<{
  "update:categoryId": [value: string];
  "update:systemCategory": [value: string];
  "update:useSystemCategory": [value: boolean];
}>();

const visibleCategories = computed(() =>
  props.categories.filter(
    (category) => props.showHidden || !category.is_hidden,
  ),
);

const systemOptions = [
  "TX_AVAILABLE_TO_BUDGET",
  "TX_STARTING_BALANCE",
  "TX_ACCOUNT_TRANSFER",
  "TX_BALANCE_ADJUSTMENT",
];
</script>

<template>
  <div class="field-stack">
    <label class="toggle">
      <input
        :checked="useSystemCategory"
        type="checkbox"
        @change="
          emit(
            'update:useSystemCategory',
            ($event.target as HTMLInputElement).checked,
          )
        "
      />
      <span>System transaction</span>
    </label>
    <label v-if="useSystemCategory" class="field">
      <span>System category</span>
      <select
        :value="systemCategory"
        @change="
          emit(
            'update:systemCategory',
            ($event.target as HTMLSelectElement).value,
          )
        "
      >
        <option value="">Select system category</option>
        <option v-for="option in systemOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
    </label>
    <CategorySelect
      v-else
      :categories="visibleCategories"
      :model-value="categoryId"
      :show-hidden="showHidden"
      @update:model-value="emit('update:categoryId', $event)"
    />
  </div>
</template>

<style scoped>
.field-stack {
  display: grid;
  gap: 0.5rem;
}
</style>
