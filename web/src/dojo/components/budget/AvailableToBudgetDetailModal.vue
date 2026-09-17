<script setup lang="ts">
import type { AvailableToBudgetBreakdown } from "../../types";
import { formatCurrency, formatMonth } from "../../utils/currency";

import Button from "../actions/Button.vue";
import LargeDetailModal from "../overlays/LargeDetailModal.vue";
import TableShell from "../tables/TableShell.vue";

defineProps<{
  visible: boolean;
  headerTotal: number;
  breakdown: AvailableToBudgetBreakdown | null;
  loading: boolean;
  error: string | null;
}>();

const emit = defineEmits<{
  close: [];
  retry: [];
}>();

const contributionColumns = [
  { key: "date", label: "Date", width: "105px" },
  { key: "source", label: "Source" },
  { key: "account", label: "Account" },
  { key: "category", label: "Category / target" },
  { key: "memo", label: "Memo" },
  { key: "amount", label: "Contribution", align: "end" as const },
  { key: "recordId", label: "Record ID" },
];

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatSignedAmount(value: number): string {
  return `${value > 0 ? "+" : ""}${formatCurrency(value)}`;
}

function directionLabel(direction: "increases" | "decreases" | "neutral") {
  if (direction === "increases") return "increases Available to budget";
  if (direction === "decreases") return "decreases Available to budget";
  return "no net change";
}

function sourceLabel(
  sourceType: string,
  origin: string | null,
  operationKind: string | null,
): string {
  const sourceLabels: Record<string, string> = {
    TX_AVAILABLE_TO_BUDGET: "Available to budget transaction",
    TX_STARTING_BALANCE: "Starting balance",
    TX_BALANCE_ADJUSTMENT: "Balance adjustment",
    BUDGET: "Budget account transfer",
    INVESTMENT: "Investment account transfer",
  };
  const provenanceLabels: Record<string, string> = {
    ACCOUNT_DETAIL: "Account detail",
    INVESTMENT_CONTRIBUTION: "Investment contribution",
    INVESTMENT_WITHDRAWAL: "Investment withdrawal",
    CREDIT_CARD_PAYMENT: "Credit card payment",
  };
  const source = sourceLabels[sourceType] ?? sourceType;
  const provenance = origin ?? operationKind;
  return provenance
    ? `${source} - ${provenanceLabels[provenance] ?? provenance}`
    : source;
}

function rowsForComponent(
  component: AvailableToBudgetBreakdown["components"][number],
) {
  return component.contributions.map((contribution) => ({
    key: contribution.id,
    date: formatDate(contribution.date),
    source: sourceLabel(
      contribution.source_type,
      contribution.origin,
      contribution.operation_kind,
    ),
    account: contribution.account_name ?? "-",
    category: contribution.category_name ?? "-",
    memo: contribution.memo || "-",
    amount: formatSignedAmount(contribution.contribution_minor),
    recordId: contribution.record_id,
  }));
}
</script>

<template>
  <LargeDetailModal
    :visible="visible"
    title="Available to budget breakdown"
    subtitle="Trace the records and allocations behind this Budget value."
    sticky
    @close="emit('close')"
  >
    <div v-if="loading" class="available-to-budget-detail__state">
      Loading explanation...
    </div>

    <div
      v-else-if="error"
      class="available-to-budget-detail__state available-to-budget-detail__state--error"
      role="alert"
      data-cy="available-to-budget-breakdown-error"
    >
      <p>We could not load the Available to budget explanation.</p>
      <p class="available-to-budget-detail__error-message">{{ error }}</p>
      <Button variant="secondary" @click="emit('retry')">Retry</Button>
    </div>

    <template v-else-if="breakdown">
      <section
        class="available-to-budget-detail__summary"
        data-cy="available-to-budget-breakdown-summary"
      >
        <div class="available-to-budget-detail__total">
          <span class="available-to-budget-detail__label"
            >Available to budget</span
          >
          <strong>{{ formatCurrency(headerTotal) }}</strong>
        </div>
        <dl class="available-to-budget-detail__context">
          <div>
            <dt>Budget period</dt>
            <dd>{{ formatMonth(breakdown.budget_month) }}</dd>
          </div>
          <div>
            <dt>Application as of</dt>
            <dd>{{ formatDate(breakdown.as_of_date) }}</dd>
          </div>
          <div>
            <dt>Calculation scope</dt>
            <dd>Current state</dd>
          </div>
        </dl>
        <p class="available-to-budget-detail__equation">
          {{
            breakdown.components
              .map(
                (component) =>
                  `${component.label}: ${formatSignedAmount(component.amount_minor)}`,
              )
              .join("  |  ")
          }}
        </p>
      </section>

      <section
        class="available-to-budget-detail__components"
        data-cy="available-to-budget-breakdown-components"
      >
        <h3>Calculation components</h3>
        <details
          v-for="component in breakdown.components"
          :key="component.key"
          class="available-to-budget-detail__component"
          open
        >
          <summary>
            <span>
              <strong>{{ component.label }}</strong>
              <small>{{ directionLabel(component.direction) }}</small>
            </span>
            <strong>{{ formatSignedAmount(component.amount_minor) }}</strong>
          </summary>
          <div class="available-to-budget-detail__contributions">
            <TableShell
              v-if="component.contributions.length > 0"
              :columns="contributionColumns"
              :rows="rowsForComponent(component)"
              sticky-header
            />
            <p v-else class="available-to-budget-detail__empty">
              No records currently contribute to this component.
            </p>
          </div>
        </details>
      </section>

      <p
        v-if="breakdown.available_to_budget_minor !== headerTotal"
        class="available-to-budget-detail__state available-to-budget-detail__state--error"
        role="alert"
      >
        The explanation changed while this surface was open. Close and reopen it
        to refresh the Budget value.
      </p>
      <p
        v-if="breakdown.available_to_budget_minor === 0"
        class="available-to-budget-detail__empty-summary"
        data-cy="available-to-budget-breakdown-empty"
      >
        Available to budget is zero. The components above show why no money is
        currently unassigned to categories.
      </p>
    </template>

    <div v-else class="available-to-budget-detail__state">
      No explanation is available.
    </div>

    <template #footer>
      <Button variant="secondary" @click="emit('close')">Close</Button>
    </template>
  </LargeDetailModal>
</template>

<style scoped>
.available-to-budget-detail__summary,
.available-to-budget-detail__components {
  display: grid;
  gap: var(--space-md);
}

.available-to-budget-detail__total {
  display: grid;
  gap: var(--space-xs);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-outline);
}

.available-to-budget-detail__total strong {
  color: var(--color-on-surface);
  font-family: var(--text-metric-lg-font-family);
  font-size: var(--text-metric-lg-font-size);
  font-weight: var(--text-metric-lg-font-weight);
  line-height: var(--text-metric-lg-line-height);
  font-feature-settings: var(--text-metric-lg-font-feature, "tnum" 1, "zero" 1);
}

.available-to-budget-detail__label,
.available-to-budget-detail__context dt,
.available-to-budget-detail__component small {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}

.available-to-budget-detail__context {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  margin: 0;
}

.available-to-budget-detail__context div {
  display: grid;
  gap: var(--space-xs);
}

.available-to-budget-detail__context dd {
  margin: 0;
  color: var(--color-on-surface);
}

.available-to-budget-detail__equation,
.available-to-budget-detail__empty,
.available-to-budget-detail__empty-summary,
.available-to-budget-detail__state,
.available-to-budget-detail__error-message {
  margin: 0;
  color: var(--color-on-surface-muted);
}

.available-to-budget-detail__equation {
  line-height: 1.6;
}

.available-to-budget-detail__components h3 {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.available-to-budget-detail__component {
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
}

.available-to-budget-detail__component summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md);
  cursor: pointer;
  color: var(--color-on-surface);
}

.available-to-budget-detail__component summary > span {
  display: grid;
  gap: var(--space-xs);
}

.available-to-budget-detail__component summary strong:last-child {
  flex-shrink: 0;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.available-to-budget-detail__contributions {
  padding: 0 var(--space-sm) var(--space-sm);
}

.available-to-budget-detail__state {
  display: grid;
  gap: var(--space-sm);
  padding: var(--space-lg);
  border: 1px solid var(--color-outline);
  background: var(--color-surface-muted);
}

.available-to-budget-detail__state--error {
  border-color: var(--color-error);
  background: var(--color-error-container);
  color: var(--color-on-surface);
}

@media (max-width: 639px) {
  .available-to-budget-detail__context {
    grid-template-columns: 1fr;
  }
}
</style>
