<script setup lang="ts">
import { computed } from "vue";

import AvailableToBudgetCard from "../components/AvailableToBudgetCard.vue";
import BudgetMonthSelector from "../components/BudgetMonthSelector.vue";
import CategoryGroupPanel from "../components/CategoryGroupPanel.vue";
import HiddenEntitiesToggle from "../components/HiddenEntitiesToggle.vue";
import LoadingSkeleton from "../components/LoadingSkeleton.vue";
import MetricStrip from "../components/MetricStrip.vue";
import PageHeader from "../components/PageHeader.vue";
import { formatMoneyMinor } from "../lib/money";
import { useAppState } from "../state/app";

const app = useAppState();

const metrics = computed(() => {
  const summary = app.state.budget?.summary;
  if (!summary) {
    return [];
  }
  return [
    { label: "Activity", value: formatMoneyMinor(summary.month_activity_minor) },
    { label: "Budgeted", value: formatMoneyMinor(summary.month_budgeted_minor) },
    { label: "Income", value: formatMoneyMinor(summary.reportable_income_minor) },
  ];
});
</script>

<template>
  <div class="page-grid">
    <PageHeader title="Budget" subtitle="Fund from ATB, move money, and preserve rollover.">
      <BudgetMonthSelector :model-value="app.state.month" @update:model-value="app.setMonth($event)" />
    </PageHeader>
    <div class="toolbar">
      <AvailableToBudgetCard :amount-minor="app.state.budget?.available_to_budget_minor ?? 0" />
      <HiddenEntitiesToggle :model-value="app.state.showHidden" @update:model-value="app.setShowHidden($event)" />
    </div>
    <MetricStrip :items="metrics" />
    <LoadingSkeleton v-if="app.state.loading && !app.state.budget" />
    <CategoryGroupPanel
      v-for="group in app.state.budget?.groups ?? []"
      :key="group.group_id"
      :all-categories="app.state.categories"
      :group="group"
      :month="app.state.month"
      @submit-allocation="app.submitAllocation($event)"
    />
  </div>
</template>

<style scoped>
.page-grid {
  display: grid;
  gap: 1rem;
}

.toolbar {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}
</style>
