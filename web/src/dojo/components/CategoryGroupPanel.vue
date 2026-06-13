<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";
import type { CategoryGroup } from "../types";
import CategoryBudgetRow from "./CategoryBudgetRow.vue";

defineProps<{
  group: CategoryGroup;
  month: string;
  allCategories: CategoryGroup["categories"];
}>();

const emit = defineEmits<{
  submitAllocation: [
    payload: {
      date: string;
      amount_minor: number;
      memo: string;
      from_bucket_id: string;
      to_bucket_id: string;
      path:
        | "/api/allocations/fund"
        | "/api/allocations/move"
        | "/api/allocations/return-to-atb";
    },
  ];
}>();
</script>

<template>
  <section class="group-panel">
    <header class="group-header">
      <div>
        <h2>{{ group.name }}</h2>
        <p>{{ group.categories.length }} categories</p>
      </div>
      <div class="group-total">
        <span>Group Total</span>
        <strong>{{ formatMoneyMinor(group.totals.available_minor) }}</strong>
      </div>
    </header>
    <div class="summary summary-header" aria-hidden="true">
      <strong>Category</strong>
      <strong>Starting available</strong>
      <strong>Budgeted</strong>
      <strong>Activity</strong>
      <strong>Available</strong>
      <strong>Actions</strong>
    </div>
    <CategoryBudgetRow
      v-for="category in group.categories"
      :key="category.category_id"
      :categories="allCategories"
      :category="category"
      :month="month"
      @submit-allocation="emit('submitAllocation', $event)"
    />
    <div class="summary summary-footer">
      <strong>Group Total</strong>
      <span>{{ formatMoneyMinor(group.totals.starting_available_minor) }}</span>
      <span>{{ formatMoneyMinor(group.totals.month_budgeted_minor) }}</span>
      <span>{{ formatMoneyMinor(group.totals.month_activity_minor) }}</span>
      <span class="available">{{
        formatMoneyMinor(group.totals.available_minor)
      }}</span>
      <span></span>
    </div>
  </section>
</template>

<style scoped>
.group-panel {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-off-white);
  padding: 1rem;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}

h2,
p {
  margin: 0;
}

.group-total {
  display: grid;
  gap: 0.15rem;
  justify-items: end;
}

.group-total span,
.group-total strong,
.summary {
  font-family: var(--dojo-mono-font);
}

.group-total span {
  font-size: 0.75rem;
  text-transform: uppercase;
}

.summary {
  display: grid;
  grid-template-columns: 1.4fr repeat(4, minmax(0, 1fr)) auto;
  gap: 0.5rem;
  align-items: center;
}

.summary-header,
.summary-footer {
  padding: 0.5rem 0;
}

.summary-header {
  border-top: 1px solid var(--dojo-border-tan);
  border-bottom: 1px solid var(--dojo-border-tan);
  font-size: 0.8rem;
  text-transform: uppercase;
}

.summary-footer {
  border-top: 1px solid var(--dojo-border-tan);
}

.summary span,
.summary strong {
  text-align: right;
}

.summary span:first-child,
.summary strong:first-child {
  text-align: left;
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
