<script setup lang="ts">
import { computed, ref } from "vue";

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
  activityFilter?: "all" | "spending" | "transfers";
  lockedAccountId?: string;
}>();

const expanded = ref(false);

const emit = defineEmits<{
  "update:accountFilter": [value: string];
  "update:dateFilter": [value: string];
  "update:categoryFilter": [value: string];
  "update:amountFilter": [value: string];
  "update:statusFilter": [value: string];
  "update:activityFilter": [value: "all" | "spending" | "transfers"];
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

const activityOptions = [
  { value: "all", label: "All activity" },
  { value: "spending", label: "Spending & income" },
  { value: "transfers", label: "Transfers" },
];

const activeFilters = computed(() => {
  const filters = [
    {
      key: "account",
      label: "Account",
      value: props.accountFilter,
      options: accountOptions.value,
    },
    {
      key: "date",
      label: "Date",
      value: props.dateFilter,
      options: dateOptions,
    },
    {
      key: "category",
      label: "Category",
      value: props.categoryFilter,
      options: categoryOptions.value,
    },
    {
      key: "amount",
      label: "Amount",
      value: props.amountFilter,
      options: amountOptions,
    },
    {
      key: "status",
      label: "Status",
      value: props.statusFilter,
      options: statusOptions,
    },
    {
      key: "activity",
      label: "Activity",
      value: props.activityFilter ?? "all",
      options: activityOptions,
    },
  ];
  return filters
    .filter(
      (filter) =>
        filter.value !== "all" &&
        !(filter.key === "account" && props.lockedAccountId),
    )
    .map((filter) => ({
      ...filter,
      selectedLabel:
        filter.options.find((option) => option.value === filter.value)?.label ??
        filter.value,
    }));
});

function clearFilter(key: string) {
  const updates: Record<string, () => void> = {
    account: () => updateAccountFilter("all"),
    date: () => updateDateFilter("all"),
    category: () => updateCategoryFilter("all"),
    amount: () => updateAmountFilter("all"),
    status: () => updateStatusFilter("all"),
    activity: () => updateActivityFilter("all"),
  };
  updates[key]?.();
}

function clearAllFilters() {
  for (const filter of activeFilters.value) clearFilter(filter.key);
}

const filterFields = computed(() => [
  {
    key: "account",
    label: "Account",
    value: props.accountFilter,
    options: accountOptions.value,
    update: updateAccountFilter,
    hidden: Boolean(props.lockedAccountId),
  },
  {
    key: "date",
    label: "Date",
    value: props.dateFilter,
    options: dateOptions,
    update: updateDateFilter,
  },
  {
    key: "category",
    label: "Category",
    value: props.categoryFilter,
    options: categoryOptions.value,
    update: updateCategoryFilter,
  },
  {
    key: "amount",
    label: "Amount",
    value: props.amountFilter,
    options: amountOptions,
    update: updateAmountFilter,
  },
  {
    key: "status",
    label: "Status",
    value: props.statusFilter,
    options: statusOptions,
    update: updateStatusFilter,
  },
  {
    key: "activity",
    label: "Activity",
    value: props.activityFilter ?? "all",
    options: activityOptions,
    update: updateActivityFilter,
  },
]);

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

function updateActivityFilter(value: string) {
  if (value === "spending" || value === "transfers") {
    emit("update:activityFilter", value);
  } else {
    emit("update:activityFilter", "all");
  }
}
</script>

<template>
  <div class="filter-bar filter-bar--compact" data-cy="transaction-filter-bar">
    <div class="filter-bar__header">
      <button
        class="filter-bar__toggle"
        type="button"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <span aria-hidden="true">☷</span>
        Filters
        <span v-if="activeFilters.length" class="filter-bar__count">{{
          activeFilters.length
        }}</span>
        <span class="filter-bar__chevron" aria-hidden="true">{{
          expanded ? "−" : "+"
        }}</span>
      </button>
      <span class="filter-bar__hint">{{
        activeFilters.length
          ? `${activeFilters.length} applied`
          : "Refine results"
      }}</span>
    </div>
    <div v-if="expanded" class="filter-bar__controls">
      <div v-if="lockedAccountId" class="filter-bar__locked-account">
        <span class="filter-bar__locked-label">Account</span>
        <span class="filter-bar__locked-value">{{ lockedAccountName }}</span>
      </div>
      <SelectField
        v-for="field in filterFields.filter((item) => !item.hidden)"
        :key="field.key"
        :model-value="field.value"
        :label="field.label"
        :options="field.options"
        @update:model-value="field.update"
      />
    </div>
    <div v-if="activeFilters.length" class="filter-bar__active">
      <span class="filter-bar__active-label">Applied</span>
      <span
        v-for="filter in activeFilters"
        :key="filter.key"
        class="filter-bar__chip"
      >
        {{ filter.label }}: {{ filter.selectedLabel }}
        <button
          type="button"
          :aria-label="`Remove ${filter.label} filter`"
          @click="clearFilter(filter.key)"
        >
          ×
        </button>
      </span>
      <button class="filter-bar__clear" type="button" @click="clearAllFilters">
        Clear all
      </button>
    </div>
    <p v-else class="filter-bar__empty">No filters applied</p>
  </div>
</template>

<style scoped>
.filter-bar {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.filter-bar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.filter-bar__toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  min-height: 36px;
  padding: 0 var(--space-md);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.filter-bar__count {
  display: inline-grid;
  min-width: 20px;
  height: 20px;
  place-items: center;
  border-radius: var(--radius-full);
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: var(--text-caption-font-size);
}

.filter-bar__chevron,
.filter-bar__hint,
.filter-bar__empty,
.filter-bar__active-label {
  color: var(--color-on-surface-muted);
}

.filter-bar__controls {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--space-md);
  align-items: end;
  padding-top: var(--space-lg);
}

.filter-bar__active {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding-top: var(--space-md);
}

.filter-bar__active-label,
.filter-bar__clear {
  font-size: var(--text-label-sm-font-size);
}

.filter-bar__chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-full);
  background: var(--color-surface-selected);
  color: var(--color-on-surface);
  font-size: var(--text-body-sm-font-size);
}

.filter-bar__chip button,
.filter-bar__clear {
  border: 0;
  background: transparent;
  color: var(--color-on-surface-muted);
  cursor: pointer;
}

.filter-bar__empty {
  margin: var(--space-sm) 0 0;
  font-size: var(--text-body-sm-font-size);
}

.filter-bar--compact {
  background: transparent;
  border: 0;
  padding: 0;
}

.filter-bar--compact .filter-bar__controls {
  margin-top: var(--space-sm);
  padding: var(--space-lg);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-popover);
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
  .filter-bar__controls {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .filter-bar__controls {
    grid-template-columns: 1fr;
  }
}
</style>
