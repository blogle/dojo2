<script setup lang="ts">
import {
  PhArrowsLeftRight,
  PhBank,
  PhChartPie,
  PhCheck,
  PhFolder,
  PhInfo,
  PhTag,
  PhUser,
  PhWarning,
} from "@phosphor-icons/vue";
import { computed } from "vue";

import Button from "@/dojo/components/actions/Button.vue";
import LargeDetailModal from "@/dojo/components/overlays/LargeDetailModal.vue";
import Surface from "@/dojo/components/layout/Surface.vue";
import type { ImportResult } from "@/dojo/types";

const props = defineProps<{
  visible: boolean;
  result: ImportResult | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

function summaryNumber(key: string): string {
  const value = importSummary.value?.[key];
  return typeof value === "number" ? value.toLocaleString() : "0";
}

const importSummary = computed(
  () => props.result?.validation_report?.summary ?? props.result?.import_summary,
);

const validationSummary = computed(() => {
  if (!props.result?.validation_report) return null;
  const report = props.result.validation_report;
  return {
    passed: report.checks.filter((check) => check.passed).length,
    warnings: report.warnings.length,
    errors: report.hard_failures.length,
  };
});

const importedRecords = computed(() => [
  {
    label: "Category groups",
    value: summaryNumber("group_count"),
    icon: PhFolder,
  },
  { label: "Categories", value: summaryNumber("category_count"), icon: PhTag },
  { label: "Accounts", value: summaryNumber("account_count"), icon: PhBank },
  {
    label: "Transactions",
    value: summaryNumber("transaction_count"),
    icon: PhArrowsLeftRight,
  },
  {
    label: "Allocations",
    value: summaryNumber("allocation_count"),
    icon: PhChartPie,
  },
  {
    label: "Net worth valuations",
    value: summaryNumber("valuation_count"),
    icon: PhUser,
  },
]);

const decisionsSummary = computed(() => {
  if (!props.result?.decisions_summary) return null;
  const ds = props.result.decisions_summary;
  return [
    {
      label: "Net-worth categories matched to budget accounts",
      value: ds.duplicates_excluded,
    },
    {
      label: "Tracking accounts created from net-worth categories",
      value: ds.tracking_created,
    },
    {
      label: "Net-worth categories not imported",
      value: ds.skipped,
    },
    {
      label: "Low-confidence suggestions accepted",
      value: ds.low_confidence_accepted,
    },
  ];
});
</script>

<template>
  <LargeDetailModal
    :visible="visible"
    title="Import details"
    data-cy="import-details-modal"
    @close="emit('close')"
  >
    <div class="import-details">
      <div
        v-if="importSummary || validationSummary || decisionsSummary"
        class="import-details__columns"
      >
        <section v-if="importSummary" class="import-details__section">
          <h3 class="import-details__heading">Imported records</h3>
          <Surface variant="raised" padding="0" :border="true">
            <div class="import-details__record-list" data-cy="import-records">
              <div
                v-for="record in importedRecords"
                :key="record.label"
                class="import-details__record-row"
              >
                <span class="import-details__record-label">
                  <component :is="record.icon" :size="16" weight="regular" />
                  <span>{{ record.label }}</span>
                </span>
                <span>{{ record.value }}</span>
              </div>
            </div>
          </Surface>
        </section>

        <section
          v-if="validationSummary || decisionsSummary"
          class="import-details__section"
        >
          <h3 v-if="validationSummary" class="import-details__heading">
            Validation summary
          </h3>
          <Surface
            v-if="validationSummary"
            variant="raised"
            padding="0"
            :border="true"
            class="import-details__validation-card"
          >
            <div
              class="import-details__validation-list"
              data-cy="validation-summary"
            >
              <div class="import-details__validation-row">
                <span
                  class="import-details__status-icon import-details__status-icon--positive"
                  aria-hidden="true"
                >
                  <PhCheck :size="18" weight="bold" />
                </span>
                <span>{{ validationSummary.passed }} checks passed</span>
              </div>
              <div class="import-details__validation-row">
                <span
                  class="import-details__status-icon import-details__status-icon--warning"
                  aria-hidden="true"
                >
                  <PhWarning :size="18" weight="fill" />
                </span>
                <span>{{ validationSummary.warnings }} warnings</span>
              </div>
              <div class="import-details__validation-row">
                <span
                  class="import-details__status-icon import-details__status-icon--neutral"
                  aria-hidden="true"
                >
                  <PhInfo :size="18" />
                </span>
                <span>{{ validationSummary.errors }} blocking issues</span>
              </div>
            </div>
          </Surface>

          <template v-else-if="decisionsSummary">
            <h3 class="import-details__heading">Review decisions</h3>
            <Surface variant="raised" padding="0" :border="true">
              <div class="import-details__record-list" data-cy="decisions-summary">
                <div
                  v-for="item in decisionsSummary"
                  :key="item.label"
                  class="import-details__record-row"
                >
                  <span class="import-details__record-label">
                    <span>{{ item.label }}</span>
                  </span>
                  <span>{{ item.value }}</span>
                </div>
              </div>
            </Surface>
          </template>

          <template v-if="validationSummary && validationSummary.warnings > 0">
            <h4 class="import-details__subheading">Warnings (non-blocking)</h4>
            <Surface variant="raised" padding="0" :border="true">
              <div class="import-details__warning-list" data-cy="warning-list">
                <div
                  v-for="(warning, index) in result?.validation_report?.warnings"
                  :key="`${warning.code}-${index}`"
                  class="import-details__warning-row"
                >
                  <span
                    class="import-details__warning-dot"
                    aria-hidden="true"
                  />
                  <span class="import-details__warning-message">
                    {{ warning.message }}
                  </span>
                </div>
              </div>
            </Surface>
          </template>
        </section>
      </div>

      <template v-if="validationSummary && decisionsSummary">
        <section class="import-details__section">
          <h3 class="import-details__heading">Review decisions</h3>
          <Surface variant="raised" padding="0" :border="true">
            <div class="import-details__record-list" data-cy="decisions-summary">
              <div
                v-for="item in decisionsSummary"
                :key="item.label"
                class="import-details__record-row"
              >
                <span class="import-details__record-label">
                  <span>{{ item.label }}</span>
                </span>
                <span>{{ item.value }}</span>
              </div>
            </div>
          </Surface>
        </section>
      </template>
    </div>

    <template #footer>
      <Button variant="primary" @click="emit('close')">Close</Button>
    </template>
  </LargeDetailModal>
</template>

<style scoped>
.import-details {
  display: grid;
  gap: var(--space-lg);
}

.import-details__columns {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-xl);
  align-items: start;
}

.import-details__section {
  display: grid;
  gap: var(--space-md);
}

.import-details__heading,
.import-details__subheading {
  margin: 0;
  color: var(--color-on-surface);
}

.import-details__heading {
  font-family: var(--text-label-lg-font-family);
  font-size: var(--text-label-lg-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-label-lg-line-height);
}

.import-details__subheading {
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.import-details__record-list,
.import-details__validation-list,
.import-details__warning-list {
  display: grid;
  margin: 0;
  padding: 0;
}

.import-details__record-row,
.import-details__validation-row,
.import-details__warning-row {
  min-height: 44px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
}

.import-details__record-row {
  justify-content: space-between;
}

.import-details__record-row + .import-details__record-row,
.import-details__validation-row + .import-details__validation-row,
.import-details__warning-row + .import-details__warning-row {
  border-top: 1px solid var(--color-outline);
}

.import-details__record-label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.import-details__record-row span:first-child,
.import-details__warning-message,
.import-details__validation-row {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.import-details__record-row span:last-child {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.import-details__validation-row,
.import-details__warning-message {
  color: var(--color-on-surface);
}

.import-details__status-icon {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.import-details__status-icon svg {
  width: 18px;
  height: 18px;
}

.import-details__status-icon--positive {
  color: var(--color-positive);
}

.import-details__status-icon--warning {
  color: var(--color-warning);
}

.import-details__status-icon--neutral {
  color: var(--color-on-surface-muted);
}

.import-details__warning-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--color-warning);
  flex: 0 0 auto;
}

@media (max-width: 600px) {
  .import-details__columns {
    grid-template-columns: 1fr;
  }
}
</style>
