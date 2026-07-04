<script setup lang="ts">
import { computed, ref } from "vue";

import type { Account, Category } from "../../types";
import SelectField from "../forms/SelectField.vue";

const props = defineProps<{
  accounts: Account[];
  categories: Category[];
}>();

const emit = defineEmits<{
  "update:accountFilter": [value: string];
  "update:dateFilter": [value: string];
  "update:categoryFilter": [value: string];
  "update:amountFilter": [value: string];
  "update:statusFilter": [value: string];
  "update:displayOrder": [value: string];
  "update:reconciliationFilter": [value: boolean];
}>();

const accountFilter = ref("all");
const dateFilter = ref("all");
const categoryFilter = ref("all");
const amountFilter = ref("all");
const statusFilter = ref("all");
const displayOrder = ref("newest");
const reconciliationFilter = ref(false);

const accountOptions = computed(() => [
  { value: "all", label: "All accounts" },
  ...props.accounts.map((a) => ({ value: a.account_id, label: a.name })),
]);

const dateOptions = [
  { value: "all", label: "All dates" },
  { value: "today", label: "Today" },
  { value: "this-week", label: "This week" },
  { value: "this-month", label: "This month" },
  { value: "last-month", label: "Last month" },
  { value: "custom", label: "Custom range" },
];

const categoryOptions = computed(() => [
  { value: "all", label: "All categories" },
  ...props.categories
    .filter((c) => c.is_active && !c.is_hidden)
    .map((c) => ({ value: c.category_id, label: c.name })),
]);

const amountOptions = [
  { value: "all", label: "Any amount" },
  { value: "0-50", label: "$0 – $50" },
  { value: "50-100", label: "$50 – $100" },
  { value: "100-500", label: "$100 – $500" },
  { value: "500+", label: "$500+" },
];

const statusOptions = [
  { value: "all", label: "All statuses" },
  { value: "cleared", label: "Cleared" },
  { value: "pending", label: "Pending" },
];

const displayOptions = [
  { value: "newest", label: "Newest first" },
  { value: "oldest", label: "Oldest first" },
];

function updateAccountFilter(value: string) {
  accountFilter.value = value;
  emit("update:accountFilter", value);
}

function updateDateFilter(value: string) {
  dateFilter.value = value;
  emit("update:dateFilter", value);
}

function updateCategoryFilter(value: string) {
  categoryFilter.value = value;
  emit("update:categoryFilter", value);
}

function updateAmountFilter(value: string) {
  amountFilter.value = value;
  emit("update:amountFilter", value);
}

function updateStatusFilter(value: string) {
  statusFilter.value = value;
  emit("update:statusFilter", value);
}

function updateDisplayOrder(value: string) {
  displayOrder.value = value;
  emit("update:displayOrder", value);
}

function toggleReconciliation() {
  reconciliationFilter.value = !reconciliationFilter.value;
  emit("update:reconciliationFilter", reconciliationFilter.value);
}
</script>

<template>
  <div class="filter-bar" data-cy="transaction-filter-bar">
    <div class="filter-bar__row">
      <SelectField
        :model-value="accountFilter"
        label="Account"
        :options="accountOptions"
        @update:model-value="updateAccountFilter"
      />
      <SelectField
        :model-value="dateFilter"
        label="Date"
        :options="dateOptions"
        @update:model-value="updateDateFilter"
      />
      <SelectField
        :model-value="categoryFilter"
        label="Category"
        :options="categoryOptions"
        @update:model-value="updateCategoryFilter"
      />
      <SelectField
        :model-value="amountFilter"
        label="Amount"
        :options="amountOptions"
        @update:model-value="updateAmountFilter"
      />
      <SelectField
        :model-value="statusFilter"
        label="Status"
        :options="statusOptions"
        @update:model-value="updateStatusFilter"
      />
      <div class="filter-bar__toggle">
        <span class="filter-bar__toggle-label"
          >Changes since last reconciliation</span
        >
        <label class="filter-bar__switch">
          <input
            type="checkbox"
            :checked="reconciliationFilter"
            @change="toggleReconciliation"
          />
          <span class="filter-bar__switch-slider" />
        </label>
      </div>
      <SelectField
        :model-value="displayOrder"
        label="Display"
        :options="displayOptions"
        @update:model-value="updateDisplayOrder"
      />
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  padding: var(--space-md) var(--space-lg);
}

.filter-bar__row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr auto 1fr;
  gap: var(--space-md);
  align-items: end;
}

.filter-bar__toggle {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.filter-bar__toggle-label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.filter-bar__switch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
}

.filter-bar__switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.filter-bar__switch-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--color-outline);
  border-radius: 10px;
  transition: background var(--transition-fast) var(--transition-ease-out);
}

.filter-bar__switch-slider::before {
  content: "";
  position: absolute;
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background: var(--color-surface);
  border-radius: 50%;
  transition: transform var(--transition-fast) var(--transition-ease-out);
}

.filter-bar__switch input:checked + .filter-bar__switch-slider {
  background: var(--color-primary);
}

.filter-bar__switch input:checked + .filter-bar__switch-slider::before {
  transform: translateX(16px);
}

@media (max-width: 1200px) {
  .filter-bar__row {
    grid-template-columns: 1fr 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .filter-bar__row {
    grid-template-columns: 1fr;
  }
}
</style>
