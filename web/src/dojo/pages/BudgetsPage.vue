<script setup lang="ts">
import { computed, ref } from "vue";
import { useQuery, useMutation, useQueryClient } from "@tanstack/vue-query";

import type { Category, CategoryGroup } from "../types";
import { formatCurrency, formatMonth } from "../utils/currency";
import {
  fetchBudget,
  fetchAllocations,
  fetchCategoryActivity,
  fetchCategories,
  fundCategory,
  fundGroup,
  createAllocation,
  createCategory,
  updateCategory,
  createCategoryGroup,
  updateCategoryGroup,
  type CategoryCreatePayload,
  type CategoryUpdatePayload,
  type CategoryGroupCreatePayload,
  type CategoryGroupUpdatePayload,
} from "../api/client";

import Button from "../components/actions/Button.vue";
import DropdownButton from "../components/actions/DropdownButton.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import PageHeader from "../components/data/PageHeader.vue";
import PersistentWarningBanner from "../components/feedback/PersistentWarningBanner.vue";
import HistoricalBanner from "../components/feedback/HistoricalBanner.vue";
import ReorderModeBanner from "../components/feedback/ReorderModeBanner.vue";
import GoalEditor from "../components/budget/GoalEditor.vue";
import IconPicker from "../components/forms/IconPicker.vue";
import NavigationRail from "../components/navigation/NavigationRail.vue";
import HierarchicalCategoryTable from "../components/tables/HierarchicalCategoryTable.vue";
import type { HierarchicalCategoryRow } from "../components/tables/HierarchicalCategoryTable.vue";
import FormModal from "../components/overlays/FormModal.vue";
import LargeDetailModal from "../components/overlays/LargeDetailModal.vue";
import TextField from "../components/forms/TextField.vue";
import SelectField from "../components/forms/SelectField.vue";
import CategoryDetailModal from "../components/budget/CategoryDetailModal.vue";
import MoveFundsModal from "../components/budget/MoveFundsModal.vue";
import FundGroupModal from "../components/budget/FundGroupModal.vue";
import FundingModal from "../components/budget/FundingModal.vue";

const queryClient = useQueryClient();

const QUERY_KEYS = {
  budget: ["budget"] as const,
  allocations: ["allocations"] as const,
  categoryActivity: ["category-activity"] as const,
} as const;

const currentMonth = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
});

const selectedMonth = ref(currentMonth.value);

const isReordering = ref(false);
const reorderChanges = ref<
  Array<{ key: string; targetKey: string; position: "before" | "after" }>
>([]);
type ReorderGroup = { groupId: string; categoryIds: string[] };
const reorderDraft = ref<ReorderGroup[]>([]);
const mutationError = ref("");
const activeModal = ref<
  | null
  | "add-group"
  | "add-category"
  | "edit-category"
  | "category-detail"
  | "group-detail"
  | "fund-group"
  | "move-funds"
  | "retired"
  | "funding"
>(null);
const selectedCategory = ref<Category | null>(null);
const selectedGroup = ref<CategoryGroup | null>(null);
const fundingCategory = ref<Category | null>(null);
const fundingOperationId = ref("");
const moveOperationId = ref("");
const groupFundingOperationId = ref("");

const groupName = ref("");
const categoryName = ref("");
const categoryGroupId = ref("");
const categoryIcon = ref("");
const goalType = ref<string | null>(null);
const goalAmountMinor = ref<number | null>(null);
const goalFrequency = ref<string | null>(null);
const goalDueDate = ref<string | null>(null);

const isHistorical = computed(
  () =>
    selectedMonth.value !== "" && selectedMonth.value !== currentMonth.value,
);

const navItems = computed(() => [
  {
    kind: "route" as const,
    key: "home",
    label: "Dashboard",
    icon: "dashboard",
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
    key: "assets-liabilities",
    label: "Assets & Liabilities",
    icon: "assets",
    href: "/assets-liabilities",
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

function computeStates(cat: Category): Array<{
  label: string;
  variant: "positive" | "warning" | "error" | "info";
}> {
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

// --- Queries ---

const { data: budgetResponse } = useQuery({
  queryKey: QUERY_KEYS.budget,
  queryFn: () => fetchBudget(selectedMonth.value, false),
});

const { data: allocations } = useQuery({
  queryKey: QUERY_KEYS.allocations,
  queryFn: () => fetchAllocations(false),
});

const { data: categoryActivity } = useQuery({
  queryKey: QUERY_KEYS.categoryActivity,
  queryFn: fetchCategoryActivity,
});

const { data: hiddenCategoriesResponse } = useQuery({
  queryKey: computed(() => ["categories", selectedMonth.value, "with-hidden"]),
  queryFn: () => fetchCategories(selectedMonth.value, true),
});

const budget = computed(() => budgetResponse.value ?? null);
const categoryGroups = computed(() => budget.value?.groups ?? []);
const categories = computed(
  () => budget.value?.groups.flatMap((g) => g.categories) ?? [],
);

// --- Mutations ---

function invalidateBudgetQueries() {
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.budget });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allocations });
}

type CategoryMutationRequest =
  | { payload: CategoryCreatePayload; categoryId?: undefined }
  | { payload: CategoryUpdatePayload; categoryId: string };

const categoryMutation = useMutation({
  mutationFn: (request: CategoryMutationRequest) =>
    "categoryId" in request
      ? updateCategory(request.categoryId!, request.payload)
      : createCategory(request.payload),
  onSuccess: () => invalidateBudgetQueries(),
  onError: (error) => {
    mutationError.value =
      error instanceof Error ? error.message : "Category change failed.";
  },
});

type CategoryGroupMutationRequest =
  | { payload: CategoryGroupCreatePayload; groupId?: undefined }
  | { payload: CategoryGroupUpdatePayload; groupId: string };

const categoryGroupMutation = useMutation({
  mutationFn: (request: CategoryGroupMutationRequest) =>
    "groupId" in request
      ? updateCategoryGroup(request.groupId!, request.payload)
      : createCategoryGroup(request.payload),
  onSuccess: () => invalidateBudgetQueries(),
  onError: (error) => {
    mutationError.value =
      error instanceof Error ? error.message : "Category group change failed.";
  },
});

const fundCategoryMutation = useMutation({
  mutationFn: ({
    categoryId,
    amountMinor,
  }: {
    categoryId: string;
    amountMinor: number;
  }) =>
    fundCategory({
      client_operation_id: fundingOperationId.value,
      date: `${selectedMonth.value || currentMonth.value}-01`,
      category_id: categoryId,
      amount_minor: amountMinor,
      memo: `Fund ${categories.value.find((item) => item.category_id === categoryId)?.name ?? "category"}`,
    }),
  onSuccess: () => {
    invalidateBudgetQueries();
    closeModal();
  },
});

// --- Derived data ---

const tableRows = computed<HierarchicalCategoryRow[]>(() => {
  if (!budget.value) return [];
  return budget.value.groups.map((group) => ({
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
      icon: cat.icon || "\u2022",
      cells: {
        goal: cat.goal_type
          ? formatCurrency(cat.goal_amount_minor ?? 0)
          : "\u2014",
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
  if (!budget.value) {
    return [
      { key: "month", label: "Month", value: "\u2014" },
      { key: "atb", label: "Available to budget", value: "\u2014" },
      { key: "activity", label: "Activity", value: "\u2014" },
      { key: "budgeted", label: "Budgeted", value: "\u2014" },
    ];
  }
  const b = budget.value;
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
  () => budget.value?.unconfigured_goal_count ?? 0,
);

const negativeAtb = computed(
  () => budget.value != null && budget.value.available_to_budget_minor < 0,
);

const retiredCategories = computed(() =>
  (hiddenCategoriesResponse.value?.items ?? []).filter((c) => c.is_hidden),
);

const selectedGroupDetail = computed<Category | null>(() => {
  if (!selectedGroup.value) return null;
  const group = selectedGroup.value;
  const monthlyGoal = group.categories.reduce(
    (total, category) => total + (category.goal_amount_minor ?? 0),
    0,
  );
  const monthlyFunding = group.categories.reduce(
    (total, category) => total + category.monthly_funding_minor,
    0,
  );
  return {
    category_id: group.group_id,
    bucket_id: group.group_id,
    group_id: group.group_id,
    group_name: "Category group",
    name: group.name,
    category_kind: "STANDARD",
    sort_order: group.sort_order,
    is_hidden: group.is_hidden,
    is_active: true,
    target_amount_minor: null,
    due_date_rule: null,
    goal_type: monthlyGoal > 0 ? "GROUP_AGGREGATE" : null,
    goal_amount_minor: monthlyGoal > 0 ? monthlyGoal : null,
    goal_frequency: null,
    goal_due_date: null,
    available_minor: group.totals.available_minor,
    month_activity_minor: group.totals.month_activity_minor,
    month_budgeted_minor: group.totals.month_budgeted_minor,
    starting_available_minor: group.totals.starting_available_minor,
    monthly_funding_minor: monthlyFunding,
    icon: group.is_system ? "\u24B8" : "\u2302",
  };
});

const selectedDetailCategory = computed(
  () => selectedCategory.value ?? selectedGroupDetail.value,
);

const selectedDetailScopeCategoryIds = computed(() => {
  if (selectedCategory.value) return [selectedCategory.value.category_id];
  if (selectedGroup.value) {
    return selectedGroup.value.categories.map(
      (category) => category.category_id,
    );
  }
  return [];
});

const firstUnconfiguredGoalCategory = computed(
  () =>
    categories.value.find(
      (category) =>
        category.category_kind === "STANDARD" && category.goal_type == null,
    ) ?? null,
);

// --- Actions ---

function restoreCategory(categoryId: string) {
  mutationError.value = "";
  categoryMutation.mutate(
    { payload: { is_hidden: false }, categoryId },
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["categories"] });
      },
    },
  );
}

function handleAdd(key: string) {
  if (key === "add-group") activeModal.value = "add-group";
  else if (key === "add-category") activeModal.value = "add-category";
}

function toggleReorder() {
  if (isReordering.value) {
    cancelReorder();
    return;
  }
  reorderDraft.value = categoryGroups.value.map((group) => ({
    groupId: group.group_id,
    categoryIds: group.categories.map((category) => category.category_id),
  }));
  isReordering.value = true;
}

function handleReorder(
  key: string,
  targetKey: string,
  position: "before" | "after",
) {
  reorderChanges.value = [
    ...reorderChanges.value,
    { key, targetKey, position },
  ];
}

function handleHierarchyChange(groups: ReorderGroup[]) {
  reorderDraft.value = groups;
  reorderChanges.value = groups.flatMap((group, groupIndex) =>
    group.categoryIds.map((categoryId, categoryIndex) => ({
      key: categoryId,
      targetKey: group.groupId,
      position: (groupIndex + categoryIndex === 0 ? "before" : "after") as
        | "before"
        | "after",
    })),
  );
}

function cancelReorder() {
  isReordering.value = false;
  reorderDraft.value = [];
  reorderChanges.value = [];
}

async function saveReorder() {
  mutationError.value = "";
  const groupById = new Map(
    categoryGroups.value.map((group) => [group.group_id, group]),
  );
  try {
    for (const [groupIndex, draftGroup] of reorderDraft.value.entries()) {
      const group = groupById.get(draftGroup.groupId);
      if (!group) continue;
      if (!group.is_system && group.sort_order !== groupIndex) {
        await updateCategoryGroup(group.group_id, { sort_order: groupIndex });
      }
      for (const [
        categoryIndex,
        categoryId,
      ] of draftGroup.categoryIds.entries()) {
        const category = categories.value.find(
          (item) => item.category_id === categoryId,
        );
        if (!category || category.category_kind !== "STANDARD") continue;
        if (
          category.group_id !== draftGroup.groupId ||
          category.sort_order !== categoryIndex
        ) {
          await updateCategory(categoryId, {
            group_id: draftGroup.groupId,
            sort_order: categoryIndex,
          });
        }
      }
    }
    invalidateBudgetQueries();
    cancelReorder();
  } catch (error) {
    mutationError.value =
      error instanceof Error ? error.message : "Reordering failed.";
  }
}

function handleRowSelect(key: string) {
  if (isReordering.value) return;
  for (const group of categoryGroups.value) {
    if (group.group_id === key) {
      selectedGroup.value = group;
      activeModal.value = "group-detail";
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

function handleReviewCategories() {
  const category = firstUnconfiguredGoalCategory.value;
  if (!category) return;
  selectedCategory.value = category;
  activeModal.value = "category-detail";
}

function handleFundCategory() {
  if (selectedGroup.value) {
    groupFundingOperationId.value = crypto.randomUUID();
    activeModal.value = "fund-group";
    return;
  }
  fundingCategory.value = selectedCategory.value;
  fundingOperationId.value = crypto.randomUUID();
  activeModal.value = "funding";
}

function handleMoveFundsFromDetail() {
  moveOperationId.value = crypto.randomUUID();
  activeModal.value = "move-funds";
}

function handleEditConfig() {
  if (!selectedCategory.value) return;
  const category = selectedCategory.value;
  categoryName.value = category.name;
  categoryGroupId.value = category.group_id;
  categoryIcon.value = category.icon ?? "";
  goalType.value = category.goal_type;
  goalAmountMinor.value = category.goal_amount_minor;
  goalFrequency.value = category.goal_frequency;
  goalDueDate.value = category.goal_due_date;
  activeModal.value = "edit-category";
}

function submitFundCategory(payload: {
  categoryId: string;
  amountMinor: number;
}) {
  if (!fundingOperationId.value) return;
  fundCategoryMutation.mutate(payload);
}

function handleMonthSelect() {
  if (selectedMonth.value) {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.budget });
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allocations });
  }
}

function returnToCurrent() {
  selectedMonth.value = currentMonth.value;
}

function closeModal() {
  activeModal.value = null;
  selectedCategory.value = null;
  selectedGroup.value = null;
  fundingCategory.value = null;
  fundingOperationId.value = "";
  moveOperationId.value = "";
  groupFundingOperationId.value = "";
  groupName.value = "";
  categoryName.value = "";
  categoryGroupId.value = "";
  categoryIcon.value = "";
  goalType.value = null;
  goalAmountMinor.value = null;
  goalFrequency.value = null;
  goalDueDate.value = null;
}

function submitAddGroup() {
  if (!groupName.value.trim()) return;
  mutationError.value = "";
  const sortOrder =
    Math.max(
      -1,
      ...categoryGroups.value
        .filter((group) => !group.is_system)
        .map((g) => g.sort_order),
    ) + 1;
  categoryGroupMutation.mutate(
    { payload: { name: groupName.value.trim(), sort_order: sortOrder } },
    { onSuccess: closeModal },
  );
}

function submitAddCategory() {
  if (!categoryName.value.trim() || !categoryGroupId.value) return;
  const groupCategories = categories.value.filter(
    (item) => item.group_id === categoryGroupId.value,
  );
  const sort_order =
    Math.max(-1, ...groupCategories.map((item) => item.sort_order)) + 1;
  categoryMutation.mutate(
    {
      payload: {
        group_id: categoryGroupId.value,
        name: categoryName.value.trim(),
        icon: categoryIcon.value.trim() || null,
        sort_order,
        goal_type: goalType.value,
        goal_amount_minor: goalAmountMinor.value,
        goal_frequency: goalFrequency.value,
        goal_due_date: goalDueDate.value,
      },
    },
    { onSuccess: closeModal },
  );
}

function submitEditCategory() {
  if (
    !selectedCategory.value ||
    !categoryName.value.trim() ||
    !categoryGroupId.value
  ) {
    return;
  }
  categoryMutation.mutate(
    {
      payload: {
        group_id: categoryGroupId.value,
        name: categoryName.value.trim(),
        icon: categoryIcon.value.trim() || null,
        goal_type: goalType.value,
        goal_amount_minor: goalAmountMinor.value,
        goal_frequency: goalFrequency.value,
        goal_due_date: goalDueDate.value,
      },
      categoryId: selectedCategory.value.category_id,
    },
    { onSuccess: closeModal },
  );
}

function retireSelectedCategory() {
  if (!selectedCategory.value) return;
  categoryMutation.mutate(
    {
      payload: { is_hidden: true },
      categoryId: selectedCategory.value.category_id,
    },
    { onSuccess: closeModal },
  );
}

async function submitMoveFunds(payload: {
  from: string;
  to: string;
  amountMinor: number;
}) {
  const fromCat = categories.value.find((c) => c.category_id === payload.from);
  const toCat = categories.value.find((c) => c.category_id === payload.to);
  if (!fromCat || !toCat) return;
  mutationError.value = "";
  if (!moveOperationId.value) moveOperationId.value = crypto.randomUUID();
  try {
    await createAllocation(
      {
        client_operation_id: moveOperationId.value,
        date: `${selectedMonth.value}-01`,
        amount_minor: payload.amountMinor,
        memo: `Move funds from ${fromCat.name} to ${toCat.name}`,
        from_bucket_id: fromCat.bucket_id,
        to_bucket_id: toCat.bucket_id,
      },
      "/api/allocations/move",
    );
    invalidateBudgetQueries();
    closeModal();
  } catch (error) {
    mutationError.value =
      error instanceof Error ? error.message : "Move funds failed.";
  }
}

async function submitFundGroup(
  items: Array<{ categoryId: string; monthlyGoalMinor: number }>,
) {
  mutationError.value = "";
  if (!groupFundingOperationId.value) {
    groupFundingOperationId.value = crypto.randomUUID();
  }
  try {
    if (!selectedGroup.value) return;
    await fundGroup({
      client_operation_id: groupFundingOperationId.value,
      date: `${selectedMonth.value}-01`,
      group_id: selectedGroup.value.group_id,
      items: items.map((item) => ({
        category_id: item.categoryId,
        amount_minor: item.monthlyGoalMinor,
      })),
    });
    invalidateBudgetQueries();
    closeModal();
  } catch (error) {
    mutationError.value =
      error instanceof Error ? error.message : "Group funding failed.";
  }
}
</script>

<template>
  <div class="budgets-page" data-cy="budgets-page-root">
    <NavigationRail
      :items="navItems"
      :full-height="true"
      brand="dojo"
      aria-label="Main navigation"
    />

    <main class="budgets-page__main">
      <PersistentWarningBanner
        v-if="mutationError"
        severity="error"
        title="Budget change failed"
        :description="mutationError"
        dismissible
        @dismiss="mutationError = ''"
      />
      <PersistentWarningBanner
        v-if="unconfiguredGoalCount > 0"
        severity="warning"
        :title="`${unconfiguredGoalCount} ${unconfiguredGoalCount === 1 ? 'category needs' : 'categories need'} goal configuration`"
        description="Some categories imported from your spreadsheet don't have a goal type set. Configure goals to enable funding and progress tracking."
        primary-action="Review categories"
        @primary="handleReviewCategories"
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
        @cancel="cancelReorder"
        @save="saveReorder"
      />

      <HierarchicalCategoryTable
        :columns="columns"
        :rows="tableRows"
        expandable
        sticky-header
        :reorderable="isReordering"
        @select="handleRowSelect"
        @reorder="handleReorder"
        @hierarchy-change="handleHierarchyChange"
      />
    </main>

    <FormModal
      :visible="activeModal === 'add-group'"
      title="Add category group"
      submit-text="Save"
      @submit="submitAddGroup"
      @cancel="closeModal"
      @close="closeModal"
    >
      <TextField
        v-model="groupName"
        label="Group name"
        placeholder="e.g. Housing"
        helper="Empty category groups are valid. You can add categories later."
      />
    </FormModal>

    <FormModal
      :visible="activeModal === 'add-category'"
      title="Add category"
      submit-text="Save"
      @submit="submitAddCategory"
      @cancel="closeModal"
      @close="closeModal"
    >
      <TextField
        v-model="categoryName"
        label="Category name"
        placeholder="e.g. Groceries"
      />
      <IconPicker
        v-model="categoryIcon"
        helper="Optional. Pick an icon to make the category easier to scan."
      />
      <SelectField
        v-model="categoryGroupId"
        label="Parent group"
        :options="[
          { value: '', label: 'Choose a group...' },
          ...categoryGroups.map((g) => ({
            value: g.group_id,
            label: g.name,
          })),
        ]"
        helper="Choose where this category belongs."
      />
      <GoalEditor
        :goal-type="goalType"
        :goal-amount-minor="goalAmountMinor"
        :goal-frequency="goalFrequency"
        :goal-due-date="goalDueDate"
        :monthly-funding-minor="0"
        @update:goal-type="goalType = $event"
        @update:goal-amount-minor="goalAmountMinor = $event"
        @update:goal-frequency="goalFrequency = $event"
        @update:goal-due-date="goalDueDate = $event"
      />
    </FormModal>

    <FormModal
      :visible="activeModal === 'edit-category'"
      title="Edit category configuration"
      submit-text="Save changes"
      danger-text="Retire category"
      @submit="submitEditCategory"
      @danger="retireSelectedCategory"
      @cancel="closeModal"
      @close="closeModal"
    >
      <TextField
        v-model="categoryName"
        label="Category name"
        placeholder="e.g. Groceries"
      />
      <IconPicker
        v-model="categoryIcon"
        helper="Optional. Pick an icon to make the category easier to scan."
      />
      <SelectField
        v-model="categoryGroupId"
        label="Parent group"
        :options="[
          { value: '', label: 'Choose a group...' },
          ...categoryGroups.map((g) => ({
            value: g.group_id,
            label: g.name,
          })),
        ]"
        helper="Choose where this category belongs."
      />
      <GoalEditor
        :goal-type="goalType"
        :goal-amount-minor="goalAmountMinor"
        :goal-frequency="goalFrequency"
        :goal-due-date="goalDueDate"
        :monthly-funding-minor="selectedCategory?.monthly_funding_minor ?? 0"
        @update:goal-type="goalType = $event"
        @update:goal-amount-minor="goalAmountMinor = $event"
        @update:goal-frequency="goalFrequency = $event"
        @update:goal-due-date="goalDueDate = $event"
      />
    </FormModal>

    <CategoryDetailModal
      :visible="
        activeModal === 'category-detail' || activeModal === 'group-detail'
      "
      :category="selectedDetailCategory"
      :allocations="allocations ?? []"
      :activity="categoryActivity ?? []"
      :scope-category-ids="selectedDetailScopeCategoryIds"
      :detail-kind="activeModal === 'group-detail' ? 'group' : 'category'"
      @close="closeModal"
      @fund="handleFundCategory"
      @move-funds="handleMoveFundsFromDetail"
      @edit-config="handleEditConfig"
    />

    <FundGroupModal
      :visible="activeModal === 'fund-group'"
      :group="selectedGroup"
      :categories="categories"
      @close="closeModal"
      @submit="submitFundGroup"
    />

    <MoveFundsModal
      :visible="activeModal === 'move-funds'"
      :categories="categories"
      @close="closeModal"
      @submit="submitMoveFunds"
    />

    <FundingModal
      :visible="activeModal === 'funding'"
      :category="fundingCategory"
      :allocations="allocations ?? []"
      :budget-month="selectedMonth || currentMonth"
      :available-to-budget-minor="budget?.available_to_budget_minor ?? 0"
      :loading="fundCategoryMutation.isPending.value"
      @close="closeModal"
      @submit="submitFundCategory"
    />

    <LargeDetailModal
      :visible="activeModal === 'retired'"
      title="Retired categories"
      subtitle="Categories you've retired from your budget."
      @close="closeModal"
    >
      <p style="color: var(--color-on-surface-muted); margin: 0">
        Retired categories are hidden from the budget table. Use Restore to
        bring them back.
      </p>
      <div
        v-if="retiredCategories.length === 0"
        style="padding: var(--space-lg) 0; color: var(--color-on-surface-muted)"
      >
        No retired categories.
      </div>
      <div v-else style="display: grid; gap: var(--space-sm)">
        <div
          v-for="cat in retiredCategories"
          :key="cat.category_id"
          style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-sm);
            border: 1px solid var(--color-outline);
          "
        >
          <span>{{ cat.name }}</span>
          <Button
            variant="tertiary"
            size="sm"
            @click="restoreCategory(cat.category_id)"
          >
            Restore
          </Button>
        </div>
      </div>
      <template #footer>
        <Button variant="secondary" @click="closeModal">Close</Button>
      </template>
    </LargeDetailModal>
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
  padding: var(--space-page-block) var(--space-page-inline);
  display: grid;
  gap: var(--space-lg);
  align-content: start;
}

@media (max-width: 720px) {
  .budgets-page__main {
    padding: var(--space-md);
  }
}
</style>
