<script setup lang="ts">
import { computed } from "vue";

import type { Account, Category } from "../../types";
import SelectField from "../forms/SelectField.vue";

const props = defineProps<{
  accounts: Account[];
  categories: Category[];
  accountFilter: string;
  dateFilter: string;
  categoryFilter: string;
  amountFilter: string;
  statusFilter: string;
  lockedAccountId?: string;
}>();

const emit = defineEmits<{
  "update:accountFilter": [value: string];
  "update:dateFilter": [value: string];
  "update:categoryFilter": [value: string];
  "update:amountFilter": [value: string];
  "update:statusFilter": [value: string];
}>();

const accountOptions = computed(() => [
  { value: "all", label: "All accounts" },
  ...props.accounts.map((a) => ({ value: a.account_id, label: a.name })),
]);

const lockedAccountName = computed(
  () =>
    props.accounts.find((a) => a.account_id === props.lockedAccountId)?.name,
);

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

function updateAccountFilter(value: string) {
  emit("update:accountFilter", value);
}

function updateDateFilter(value: string) {
  emit("update:dateFilter", value);
}

function updateCategoryFilter(value: string) {
  emit("update:categoryFilter", value);
}

function updateAmountFilter(value: string) {
  emit("update:amountFilter", value);
}

function updateStatusFilter(value: string) {
  emit("update:statusFilter", value);
}
</script>

<template>
  <div class="filter-bar" data-cy="transaction-filter-bar">
    <div class="filter-bar__row">
      <div v-if="lockedAccountId" class="filter-bar__locked-account">
        <span class="filter-bar__locked-label">Account</span>
        <span class="filter-bar__locked-value">{{ lockedAccountName }}</span>
      </div>
      <SelectField
        v-else
        :model-value="props.accountFilter"
        label="Account"
        :options="accountOptions"
        @update:model-value="updateAccountFilter"
      />
      <SelectField
        :model-value="props.dateFilter"
        label="Date"
        :options="dateOptions"
        @update:model-value="updateDateFilter"
      />
      <SelectField
        :model-value="props.categoryFilter"
        label="Category"
        :options="categoryOptions"
        @update:model-value="updateCategoryFilter"
      />
      <SelectField
        :model-value="props.amountFilter"
        label="Amount"
        :options="amountOptions"
        @update:model-value="updateAmountFilter"
      />
      <SelectField
        :model-value="props.statusFilter"
        label="Status"
        :options="statusOptions"
        @update:model-value="updateStatusFilter"
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
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-md);
  align-items: end;
}

.filter-bar__locked-account {
  display: grid;
  gap: var(--space-xs);
}

.filter-bar__locked-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
}

.filter-bar__locked-value {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  padding: 0 var(--space-md);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
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
