<script setup lang="ts">
import { computed, ref } from "vue";

import type { Category } from "../../types";
import { formatCurrency, formatGoalType } from "../../utils/currency";

import Button from "../actions/Button.vue";
import KeyValueList from "../display/KeyValueList.vue";
import Tabs from "../navigation/Tabs.vue";
import FullScreenTrouser from "../overlays/FullScreenTrouser.vue";

const props = defineProps<{
  visible: boolean;
  category: Category | null;
}>();

const emit = defineEmits<{
  close: [];
  fund: [];
  "move-funds": [];
  "edit-config": [];
}>();

const activeTab = ref<"overview" | "funding-history" | "spending-history">(
  "overview",
);

const tabs = computed(() => [
  { key: "overview", label: "Overview" },
  { key: "funding-history", label: "Funding history" },
  { key: "spending-history", label: "Spending history" },
]);

const summaryMetrics = computed(() => {
  if (!props.category) return [];
  const c = props.category;
  return [
    { label: "Current available", value: formatCurrency(c.available_minor) },
    {
      label: "Monthly goal",
      value: c.goal_type ? formatCurrency(c.goal_amount_minor ?? 0) : "\u2014",
    },
    {
      label: "Budgeted this month",
      value: formatCurrency(c.month_budgeted_minor),
    },
    {
      label: "Activity this month",
      value: formatCurrency(c.month_activity_minor),
    },
  ];
});

const goalConfigItems = computed(() => {
  if (!props.category) return [];
  const c = props.category;
  return [
    {
      label: "Goal type",
      value: c.goal_type ? formatGoalType(c.goal_type) : "Not set",
    },
    {
      label: "Monthly goal",
      value: c.goal_type ? formatCurrency(c.goal_amount_minor ?? 0) : "\u2014",
    },
    { label: "Start month", value: "\u2014" },
    { label: "Target amount", value: "\u2014" },
    { label: "Target date", value: c.goal_due_date ?? "\u2014" },
    { label: "Rollover", value: "On" },
    { label: "Incremental", value: "Off" },
  ];
});

const goalProgress = computed(() => {
  if (!props.category) return null;
  const c = props.category;
  const monthlyGoal = c.goal_amount_minor ?? 0;
  if (monthlyGoal <= 0) return null;
  const available = Math.max(0, c.available_minor);
  const pct = Math.min(100, Math.round((available / monthlyGoal) * 100));
  const remaining = Math.max(0, monthlyGoal - available);
  return { pct, available, remaining, monthlyGoal };
});

const fundingToDate = computed(() => {
  if (!props.category) return null;
  const c = props.category;
  const expected = c.monthly_funding_minor;
  const actual = c.month_budgeted_minor;
  const deviation = actual - expected;
  return {
    expected,
    actual,
    deviation,
    additionalNeeded: 0,
    spendingReduction: 0,
  };
});

const fundingToDateItems = computed(() => {
  if (!fundingToDate.value) return [];
  const f = fundingToDate.value;
  return [
    { label: "Expected funding to date", value: formatCurrency(f.expected) },
    { label: "Actual funding to date", value: formatCurrency(f.actual) },
    {
      label: "Deviation from plan",
      value: `${f.deviation >= 0 ? "+" : ""}${formatCurrency(f.deviation)}`,
    },
    {
      label: "Additional monthly funding needed to recover",
      value: formatCurrency(f.additionalNeeded),
    },
    {
      label: "Spending reduction needed to recover",
      value: formatCurrency(f.spendingReduction),
    },
  ];
});
</script>

<template>
  <FullScreenTrouser
    :visible="visible"
    :title="category?.name"
    :subtitle="category?.group_name"
    @close="emit('close')"
  >
    <template #header-actions>
      <Button variant="primary" @click="emit('fund')"> Fund </Button>
      <Button variant="secondary" @click="emit('move-funds')">
        Move funds
      </Button>
      <Button variant="secondary" @click="emit('edit-config')">
        Edit configuration
      </Button>
    </template>

    <template #tabs>
      <Tabs :items="tabs" v-model="activeTab" />
    </template>

    <div v-if="activeTab === 'overview'" class="category-detail__overview">
      <div class="category-detail__metrics">
        <div
          v-for="m in summaryMetrics"
          :key="m.label"
          class="category-detail__metric"
        >
          <span class="category-detail__metric-label">{{ m.label }}</span>
          <span class="category-detail__metric-value">{{ m.value }}</span>
        </div>
      </div>

      <div class="category-detail__panels">
        <div class="category-detail__panel">
          <h3 class="category-detail__panel-title">Goal configuration</h3>
          <KeyValueList :items="goalConfigItems" />
        </div>

        <div v-if="goalProgress" class="category-detail__panel">
          <h3 class="category-detail__panel-title">Goal progress</h3>
          <div class="category-detail__progress">
            <div class="category-detail__progress-ring">
              <svg viewBox="0 0 80 80" class="category-detail__progress-svg">
                <circle
                  cx="40"
                  cy="40"
                  r="35"
                  class="category-detail__progress-track"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="35"
                  class="category-detail__progress-fill"
                  :style="{
                    strokeDasharray: `${(goalProgress.pct / 100) * 220} 220`,
                  }"
                />
              </svg>
              <span class="category-detail__progress-pct"
                >{{ goalProgress.pct }}%</span
              >
            </div>
            <div class="category-detail__progress-stats">
              <div>
                <span class="category-detail__progress-label">Available</span>
                <span
                  class="category-detail__progress-value category-detail__progress-value--positive"
                >
                  {{ formatCurrency(goalProgress.available) }}
                </span>
              </div>
              <div>
                <span class="category-detail__progress-label">Remaining</span>
                <span class="category-detail__progress-value">{{
                  formatCurrency(goalProgress.remaining)
                }}</span>
              </div>
              <div>
                <span class="category-detail__progress-label"
                  >Monthly goal</span
                >
                <span class="category-detail__progress-value">{{
                  formatCurrency(goalProgress.monthlyGoal)
                }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="fundingToDate" class="category-detail__panel">
          <h3 class="category-detail__panel-title">Funding to date</h3>
          <KeyValueList :items="fundingToDateItems" />
        </div>
      </div>
    </div>

    <div
      v-if="activeTab === 'funding-history'"
      class="category-detail__placeholder"
    >
      <p>Funding history will show a filtered view of category allocations.</p>
    </div>

    <div
      v-if="activeTab === 'spending-history'"
      class="category-detail__placeholder"
    >
      <p>Spending history will show a filtered view of transactions.</p>
    </div>

    <template #footer>
      <Button variant="secondary" @click="emit('close')">Close</Button>
    </template>
  </FullScreenTrouser>
</template>

<style scoped>
.category-detail__overview {
  display: grid;
  gap: var(--space-lg);
}

.category-detail__metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
}

.category-detail__metric {
  display: grid;
  gap: 2px;
}

.category-detail__metric-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}

.category-detail__metric-value {
  color: var(--color-on-surface);
  font-family: var(--text-metric-md-font-family);
  font-size: var(--text-metric-md-font-size);
  font-weight: var(--text-metric-md-font-weight);
  line-height: var(--text-metric-md-line-height);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.category-detail__panels {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--space-md);
}

.category-detail__panel {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  padding: var(--space-md);
}

.category-detail__panel-title {
  margin: 0 0 var(--space-sm);
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.category-detail__progress {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-md);
  align-items: center;
}

.category-detail__progress-ring {
  position: relative;
  width: 80px;
  height: 80px;
}

.category-detail__progress-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.category-detail__progress-track {
  fill: none;
  stroke: var(--color-surface-muted);
  stroke-width: 6;
}

.category-detail__progress-fill {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dasharray var(--motion-normal) var(--motion-ease-out);
}

.category-detail__progress-pct {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
}

.category-detail__progress-stats {
  display: grid;
  gap: var(--space-xs);
}

.category-detail__progress-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.category-detail__progress-value {
  display: block;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.category-detail__progress-value--positive {
  color: var(--color-positive);
}

.category-detail__placeholder {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-xl) 0;
}

.category-detail__placeholder p {
  margin: 0;
}

@media (max-width: 720px) {
  .category-detail__metrics {
    grid-template-columns: repeat(2, 1fr);
  }

  .category-detail__panels {
    grid-template-columns: 1fr;
  }
}
</style>
