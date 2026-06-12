<script setup lang="ts">
import { ref } from "vue";

import { formatMoneyMinor } from "../lib/money";
import type { Category } from "../types";
import AllocationPopover from "./AllocationPopover.vue";

defineProps<{
  category: Category;
  categories: Category[];
  month: string;
}>();

const emit = defineEmits<{ submitAllocation: [payload: { date: string; amount_minor: number; memo: string; from_bucket_id: string; to_bucket_id: string; path: "/api/allocations/fund" | "/api/allocations/move" | "/api/allocations/return-to-atb" }] }>();

const open = ref(false);
</script>

<template>
  <div class="budget-row">
    <div class="summary">
      <strong>{{ category.name }}</strong>
      <span>{{ formatMoneyMinor(category.carried_over_minor) }}</span>
      <span>{{ formatMoneyMinor(category.month_budgeted_minor) }}</span>
      <span>{{ formatMoneyMinor(category.month_activity_minor) }}</span>
      <span class="available">{{ formatMoneyMinor(category.available_minor) }}</span>
      <button type="button" @click="open = !open">Allocate</button>
    </div>
    <AllocationPopover v-if="open" :categories="categories" :category="category" :month="month" @submit="emit('submitAllocation', $event)" />
  </div>
</template>

<style scoped>
.budget-row {
  border-top: 1px solid var(--dojo-border-tan);
  padding: 0.5rem 0;
}

.summary {
  display: grid;
  grid-template-columns: 1.4fr repeat(4, minmax(0, 1fr)) auto;
  gap: 0.5rem;
  align-items: center;
}

span {
  font-family: var(--dojo-mono-font);
  text-align: right;
}

.available {
  color: var(--dojo-green-dark);
}

@media (max-width: 900px) {
  .summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
