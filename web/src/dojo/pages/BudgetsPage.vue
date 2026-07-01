<script setup lang="ts">
import { computed, ref, onMounted } from "vue";

import type { Category, CategoryGroup } from "../types";
import { useAppState } from "../state/app";
import { formatCurrency, formatMonth } from "../utils/currency";

import Button from "../components/actions/Button.vue";
import DropdownButton from "../components/actions/DropdownButton.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import PageHeader from "../components/data/PageHeader.vue";
import PersistentWarningBanner from "../components/feedback/PersistentWarningBanner.vue";
import HistoricalBanner from "../components/feedback/HistoricalBanner.vue";
import ReorderModeBanner from "../components/feedback/ReorderModeBanner.vue";
import NavigationRail from "../components/navigation/NavigationRail.vue";
import HierarchicalCategoryTable from "../components/tables/HierarchicalCategoryTable.vue";
import type { HierarchicalCategoryRow } from "../components/tables/HierarchicalCategoryTable.vue";

const {
  state,
  initialize,
  setMonth,
} = useAppState();

const selectedMonth = ref("");
const isReordering = ref(false);
const reorderChanges = ref<
  Array<{ key: string; targetKey: string; position: "before" | "after" }>
>([]);
const activeModal = ref<
  | null
  | "add-group"
  | "add-category"
  | "category-detail"
  | "fund-group"
  | "move-funds"
  | "retired"
>(null);
const selectedCategory = ref<Category | null>(null);
const selectedGroup = ref<CategoryGroup | null>(null);

const currentMonth = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
});

const isHistorical = computed(
  () => selectedMonth.value !== "" && selectedMonth.value !== currentMonth.value,
);

const navItems = computed(() => [
  {
    kind: "route" as const,
    key: "home",
    label: "Home",
    icon: "foundations",
    href: "/",
  },
  {
    kind: "route" as const,
    key: "budget",
    label: "Budget",
    icon: "budget",
    href: "/budgets",
    current: true,
  },
  {
    kind: "route" as const,
    key: "transactions",
    label: "Transactions",
    icon: "transactions",
    href: "/transactions",
  },
  {
    kind: "route" as const,
    key: "assets",
    label: "Assets",
    icon: "assets",
    href: "/assets",
  },
]);

const columns = [
  { key: "category", label: "Category" },
  { key: "goal", label: "Goal", align: "end" as const },
  { key: "dueDate", label: "Due date" },
  { key: "available", label: "Available", align: "end" as const },
  { key: "activity", label: "Activity", align: "end" as const },
  { key: "budgeted", label: "Budgeted", align: "end" as const },
];

function groupIcon(group: CategoryGroup): string {
  if (group.is_system) return "\u24B8";
  return "\u2302";
}

function formatGoalDueDate(cat: Category): string {
  if (!cat.goal_due_date) return "No due date";
  const d = new Date(cat.goal_due_date + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function computeVariants(
  cat: Category,
): Record<string, "positive" | "warning" | "error"> {
  const variants: Record<string, "positive" | "warning" | "error"> = {};
  if (cat.available_minor < 0) {
    variants.available = "error";
  }
  if (cat.month_activity_minor < 0) {
    variants.activity = "error";
  }
  return variants;
}

function computeStates(
  cat: Category,
): Array<{ label: string; variant: "positive" | "warning" | "error" | "info" }> {
  const states: Array<{
    label: string;
    variant: "positive" | "warning" | "error" | "info";
  }> = [];
  if (cat.is_hidden) {
    states.push({ label: "Retired", variant: "info" });
  }
  if (cat.available_minor < 0) {
    states.push({ label: "Overspent", variant: "error" });
  }
  return states;
}

const tableRows = computed<HierarchicalCategoryRow[]>(() => {
  if (!state.budget) return [];
  return state.budget.groups.map((group) => ({
    key: group.group_id,
    label: group.name,
    icon: groupIcon(group),
    group: true,
    cells: {
      goal: "\u2014",
      dueDate: "\u2014",
      available: formatCurrency(group.totals.available_minor),
      activity: formatCurrency(group.totals.month_activity_minor),
      budgeted: formatCurrency(group.totals.month_budgeted_minor),
    },
    children: group.categories.map((cat) => ({
      key: cat.category_id,
      label: cat.name,
      cells: {
        goal: cat.goal_type ? formatCurrency(cat.goal_amount_minor ?? 0) : "\u2014",
        dueDate: formatGoalDueDate(cat),
        available: formatCurrency(cat.available_minor),
        activity: formatCurrency(cat.month_activity_minor),
        budgeted: formatCurrency(cat.month_budgeted_minor),
      },
      cellVariants: computeVariants(cat),
      states: computeStates(cat),
    })),
  }));
});

const metrics = computed(() => {
  if (!state.budget) {
    return [
      { key: "month", label: "Month", value: "\u2014" },
      { key: "atb", label: "Available to budget", value: "\u2014" },
      { key: "activity", label: "Activity", value: "\u2014" },
      { key: "budgeted", label: "Budgeted", value: "\u2014" },
    ];
  }
  const b = state.budget;
  return [
    {
      key: "month",
      label: "Month",
      value: formatMonth(selectedMonth.value || currentMonth.value),
    },
    {
      key: "atb",
      label: "Available to budget",
      value: formatCurrency(b.available_to_budget_minor),
      status:
        b.available_to_budget_minor < 0
          ? { label: "Negative", variant: "error" as const }
          : undefined,
    },
    {
      key: "activity",
      label: "Activity",
      value: formatCurrency(b.summary.month_activity_minor),
    },
    {
      key: "budgeted",
      label: "Budgeted",
      value: formatCurrency(b.summary.month_budgeted_minor),
    },
  ];
});

const addItems = [
  { key: "add-category", label: "Add category" },
  { key: "add-group", label: "Add category group" },
];

const unconfiguredGoalCount = computed(
  () => state.budget?.unconfigured_goal_count ?? 0,
);

const negativeAtb = computed(
  () =>
    state.budget != null && state.budget.available_to_budget_minor < 0,
);

function handleAdd(key: string) {
  if (key === "add-group") activeModal.value = "add-group";
  else if (key === "add-category") activeModal.value = "add-category";
}

function toggleReorder() {
  isReordering.value = !isReordering.value;
  if (!isReordering.value) reorderChanges.value = [];
}

function handleReorder(key: string, targetKey: string, position: "before" | "after") {
  reorderChanges.value = [...reorderChanges.value, { key, targetKey, position }];
}

function handleRowSelect(key: string) {
  if (isReordering.value) return;
  for (const group of state.categoryGroups) {
    if (group.group_id === key) {
      selectedGroup.value = group;
      activeModal.value = "fund-group";
      return;
    }
    for (const cat of group.categories) {
      if (cat.category_id === key) {
        selectedCategory.value = cat;
        activeModal.value = "category-detail";
        return;
      }
    }
  }
}

function handleMonthSelect() {
  if (selectedMonth.value) {
    setMonth(selectedMonth.value);
  }
}

function returnToCurrent() {
  selectedMonth.value = currentMonth.value;
  setMonth(currentMonth.value);
}

onMounted(() => {
  initialize().then(() => {
    selectedMonth.value = state.month || currentMonth.value;
  });
});
</script>

<template>
  <div class="budgets-page" data-cy="budgets-page-root">
    <NavigationRail
      :items="navItems"
      brand="dojo"
      aria-label="Main navigation"
    />

    <main class="budgets-page__main">
      <PersistentWarningBanner
        v-if="unconfiguredGoalCount > 0"
        severity="warning"
        :title="`${unconfiguredGoalCount} ${unconfiguredGoalCount === 1 ? 'category needs' : 'categories need'} goal configuration`"
        description="Some categories imported from your spreadsheet don't have a goal type set. Configure goals to enable funding and progress tracking."
        primary-action="Review categories"
        @primary="activeModal = 'retired'"
      />

      <PersistentWarningBanner
        v-if="negativeAtb"
        severity="error"
        title="Your Available to budget is negative. Add funds or make changes to your budget to fix this."
        primary-action="Learn more"
        dismissible
      />

      <HistoricalBanner
        v-if="isHistorical"
        :description="`Showing the budget as of ${formatMonth(selectedMonth)}. Editing and funding actions are disabled in this mode.`"
        exit-label="Return to current"
        @exit="returnToCurrent"
      />

      <PageHeader title="Budget">
        <template #actions>
          <DropdownButton
            label="Add"
            :items="addItems"
            :disabled="isReordering || isHistorical"
            @select="handleAdd"
          />
          <Button
            variant="secondary"
            :disabled="isHistorical"
            @click="toggleReorder"
          >
            {{ isReordering ? "Cancel" : "Reorder" }}
          </Button>
          <Button
            variant="secondary"
            :disabled="isReordering || isHistorical"
            @click="activeModal = 'retired'"
          >
            Retired categories
          </Button>
        </template>
      </PageHeader>

      <MetricStrip :items="metrics" @select="handleMonthSelect" />

      <ReorderModeBanner
        v-if="isReordering"
        :pending-count="reorderChanges.length"
        @cancel="toggleReorder"
        @save="toggleReorder"
      />

      <HierarchicalCategoryTable
        :columns="columns"
        :rows="tableRows"
        expandable
        sticky-header
        :reorderable="isReordering"
        @select="handleRowSelect"
        @reorder="handleReorder"
      />
    </main>
  </div>
</template>

<style scoped>
.budgets-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.budgets-page__main {
  flex: 1;
  margin-left: var(--space-nav-collapsed);
  padding: var(--space-page-block) var(--space-page-inline);
  display: grid;
  gap: var(--space-lg);
  align-content: start;
}

@media (max-width: 720px) {
  .budgets-page__main {
    margin-left: 0;
    padding: var(--space-md);
  }
}
</style>
