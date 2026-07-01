<script setup lang="ts">
import { computed, ref } from "vue";

import type { Category } from "../../types";
import { formatCurrency, formatGoalType } from "../../utils/currency";

import Button from "../actions/Button.vue";
import KeyValueList from "../display/KeyValueList.vue";
import Tabs from "../navigation/Tabs.vue";
import LargeDetailModal from "../overlays/LargeDetailModal.vue";
import GoalEditor from "./GoalEditor.vue";

const props = defineProps<{
  visible: boolean;
  category: Category | null;
}>();

const emit = defineEmits<{
  close: [];
  updateGoal: [];
}>();

const activeTab = ref<"overview" | "transactions" | "goals" | "funding">(
  "overview",
);

const tabs = computed(() => [
  { key: "overview", label: "Overview" },
  { key: "transactions", label: "Transactions" },
  { key: "goals", label: "Goals" },
  { key: "funding", label: "Funding" },
]);

const overviewItems = computed(() => {
  if (!props.category) return [];
  const c = props.category;
  return [
    { label: "Available (all time)", value: formatCurrency(c.available_minor) },
    { label: "Activity", value: formatCurrency(c.month_activity_minor) },
    { label: "Budgeted", value: formatCurrency(c.month_budgeted_minor) },
    { label: "Overspent", value: formatCurrency(Math.abs(Math.min(0, c.available_minor))) },
    { label: "Goal", value: c.goal_type ? formatGoalType(c.goal_type) : "Not set" },
  ];
});
</script>

<template>
  <LargeDetailModal
    :visible="visible"
    :title="category?.name"
    :subtitle="category?.group_name"
    @close="emit('close')"
  >
    <template #tabs>
      <Tabs
        :items="tabs"
        v-model="activeTab"
      />
    </template>

    <div v-if="activeTab === 'overview'">
      <KeyValueList :items="overviewItems" />
    </div>

    <div v-if="activeTab === 'transactions'" style="color: var(--color-on-surface-muted);">
      Transactions list coming soon.
    </div>

    <div v-if="activeTab === 'goals'">
      <GoalEditor
        :goal-type="category?.goal_type ?? null"
        :goal-amount-minor="category?.goal_amount_minor ?? null"
        :goal-frequency="category?.goal_frequency ?? null"
        :goal-due-date="category?.goal_due_date ?? null"
        :monthly-funding-minor="category?.monthly_funding_minor ?? 0"
        read-only
      />
    </div>

    <div v-if="activeTab === 'funding'" style="color: var(--color-on-surface-muted);">
      Funding allocation coming soon.
    </div>

    <template #footer>
      <Button variant="secondary" @click="emit('close')">Close</Button>
    </template>
  </LargeDetailModal>
</template>
