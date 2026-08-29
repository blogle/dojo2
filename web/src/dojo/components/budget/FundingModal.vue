<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Allocation, Category } from "../../types";
import { formatCurrency, parseMoneyInput } from "../../utils/currency";

import CurrencyField from "../forms/CurrencyField.vue";
import SelectField from "../forms/SelectField.vue";
import PreviewBox from "../feedback/PreviewBox.vue";
import FormModal from "../overlays/FormModal.vue";

const props = withDefaults(
  defineProps<{
    visible: boolean;
    category: Category | null;
    allocations: Allocation[];
    budgetMonth: string;
    availableToBudgetMinor: number;
    loading?: boolean;
  }>(),
  { loading: false },
);

const emit = defineEmits<{
  close: [];
  submit: [payload: { categoryId: string; amountMinor: number }];
}>();

type FundingOption =
  | "same-as-last-month"
  | "average"
  | "next-month"
  | "monthly-goal"
  | "custom";

const selectedOption = ref<FundingOption>("same-as-last-month");
const customAmount = ref("");

const monthlyGoal = computed(() => {
  if (!props.category) return 0;
  return props.category.goal_amount_minor ?? 0;
});

const fundUpToNextMonth = computed(() => {
  if (!props.category) return 0;
  const goal = monthlyGoal.value;
  const available = props.category.available_minor;
  return Math.max(0, goal - available);
});

const fundToMonthlyGoal = computed(() => {
  return fundUpToNextMonth.value;
});

function previousMonth(month: string): string {
  const [year, monthNumber] = month.split("-").map(Number);
  const date = new Date(year, monthNumber - 2, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function allocationMonth(date: string): string {
  return date.slice(0, 7);
}

function signedAllocationAmount(allocation: Allocation): number {
  if (!props.category) return 0;
  if (allocation.to_category_id === props.category.category_id) {
    return allocation.amount_minor;
  }
  if (allocation.from_category_id === props.category.category_id) {
    return -allocation.amount_minor;
  }
  return 0;
}

const categoryAllocations = computed(() => {
  if (!props.category) return [];
  return props.allocations.filter(
    (allocation) =>
      allocation.to_category_id === props.category?.category_id ||
      allocation.from_category_id === props.category?.category_id,
  );
});

const fundSameAsLastMonth = computed(() => {
  const lastMonth = previousMonth(props.budgetMonth);
  return Math.max(
    0,
    categoryAllocations.value
      .filter((allocation) => allocationMonth(allocation.date) === lastMonth)
      .reduce(
        (total, allocation) => total + signedAllocationAmount(allocation),
        0,
      ),
  );
});

const fundAverage = computed(() => {
  const monthlyTotals = new Map<string, number>();
  for (const allocation of categoryAllocations.value) {
    const month = allocationMonth(allocation.date);
    monthlyTotals.set(
      month,
      (monthlyTotals.get(month) ?? 0) + signedAllocationAmount(allocation),
    );
  }
  const positiveTotals = [...monthlyTotals.values()].filter(
    (amount) => amount > 0,
  );
  if (positiveTotals.length === 0) {
    return props.category?.monthly_funding_minor || monthlyGoal.value;
  }
  return Math.round(
    positiveTotals.reduce((total, amount) => total + amount, 0) /
      positiveTotals.length,
  );
});

const selectedAmount = computed(() => {
  if (selectedOption.value === "same-as-last-month") {
    return fundSameAsLastMonth.value;
  }
  if (selectedOption.value === "average") return fundAverage.value;
  if (selectedOption.value === "next-month") return fundUpToNextMonth.value;
  if (selectedOption.value === "monthly-goal") return fundToMonthlyGoal.value;
  return parseMoneyInput(customAmount.value) ?? 0;
});

const currentAvailable = computed(() => props.category?.available_minor ?? 0);
const newAvailable = computed(
  () => currentAvailable.value + selectedAmount.value,
);
const currentAtb = computed(() => props.availableToBudgetMinor);
const newAtb = computed(() => currentAtb.value - selectedAmount.value);
const willBeNegative = computed(() => newAtb.value < 0);

const optionItems = computed(() => [
  {
    key: "same-as-last-month" as const,
    label: "Fund same as last month",
    description: "Use the amount budgeted to this category last month.",
    amount: fundSameAsLastMonth.value,
  },
  {
    key: "average" as const,
    label: "Fund average",
    description:
      "Use the average positive monthly funding from allocation history.",
    amount: fundAverage.value,
  },
  {
    key: "next-month" as const,
    label: "Fund up to next month",
    description:
      "Bring this category to the amount needed for the next due period.",
    amount: fundUpToNextMonth.value,
  },
  {
    key: "monthly-goal" as const,
    label: "Fund to monthly goal",
    description: "Add the remaining amount needed to reach this month's goal.",
    amount: fundToMonthlyGoal.value,
  },
  {
    key: "custom" as const,
    label: "Custom amount",
    description: "Enter a specific amount for this funding action.",
    amount: parseMoneyInput(customAmount.value) ?? 0,
  },
]);

const optionSelectItems = computed(() =>
  optionItems.value.map((option) => ({
    value: option.key,
    label: `${option.label} - ${formatCurrency(option.amount)}`,
  })),
);

const selectedOptionDescription = computed(
  () =>
    optionItems.value.find((option) => option.key === selectedOption.value)
      ?.description ?? "",
);

function handleSubmit() {
  if (!props.category || selectedAmount.value <= 0) return;
  emit("submit", {
    categoryId: props.category.category_id,
    amountMinor: selectedAmount.value,
  });
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) return;
    selectedOption.value = "same-as-last-month";
    customAmount.value = "";
  },
);
</script>

<template>
  <FormModal
    :visible="visible"
    :title="`Fund: ${category?.name ?? ''}`"
    submit-text="Save"
    :submit-disabled="selectedAmount <= 0"
    :loading="loading"
    @submit="handleSubmit"
    @cancel="emit('close')"
    @close="emit('close')"
  >
    <p class="funding-modal__subtitle">
      Monthly goal: {{ formatCurrency(monthlyGoal) }}
    </p>

    <div class="funding-modal__section">
      <p class="funding-modal__heading">Fund {{ category?.name }}</p>
      <p class="funding-modal__helper">
        Choose a funding shortcut or enter a custom amount.
      </p>
    </div>

    <div class="funding-modal__section">
      <SelectField
        v-model="selectedOption"
        label="Funding option"
        :options="optionSelectItems"
        :helper="selectedOptionDescription"
      />
      <CurrencyField
        v-if="selectedOption === 'custom'"
        v-model="customAmount"
        label="Custom amount"
        placeholder="0.00"
      />
    </div>

    <PreviewBox title="Preview" class="funding-modal__preview">
      <p class="funding-modal__preview-title">Preview</p>
      <p class="funding-modal__preview-helper">
        Review the results of this action before you save.
      </p>
      <div class="funding-modal__preview-grid">
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label">Amount being funded</span>
          <span
            class="funding-modal__preview-value funding-modal__preview-value--positive"
            >{{ formatCurrency(selectedAmount) }}</span
          >
        </div>
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label"
            >{{ category?.name }} balance</span
          >
          <span
            class="funding-modal__preview-value funding-modal__preview-value--positive"
          >
            {{ formatCurrency(currentAvailable) }} →
            {{ formatCurrency(newAvailable) }}
          </span>
        </div>
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label">Available to budget</span>
          <span
            class="funding-modal__preview-value"
            :class="{
              'funding-modal__preview-value--negative': selectedAmount > 0,
              'funding-modal__preview-value--error': willBeNegative,
            }"
          >
            {{ formatCurrency(currentAtb) }} → {{ formatCurrency(newAtb) }}
          </span>
        </div>
      </div>
      <p v-if="willBeNegative" class="funding-modal__warning">
        Available to budget will be negative after this action.
      </p>
    </PreviewBox>
  </FormModal>
</template>

<style scoped>
.funding-modal__subtitle {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.funding-modal__section {
  display: grid;
  gap: var(--space-xs);
}

.funding-modal__heading {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-label-lg-font-family);
  font-size: var(--text-label-lg-font-size);
  font-weight: var(--text-label-lg-font-weight);
}

.funding-modal__helper {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.funding-modal__field-label {
  margin: 0 0 var(--space-xs);
  color: var(--color-on-surface);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
}

.funding-modal__options {
  display: grid;
  gap: var(--space-xs);
}

.funding-modal__option {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  cursor: pointer;
  transition: background-color var(--motion-fast) var(--motion-ease-out);
}

.funding-modal__option:hover {
  background: var(--color-surface-selected);
}

.funding-modal__option--selected {
  border-color: var(--color-primary);
  background: var(--color-surface-selected);
}

.funding-modal__radio {
  margin: 0;
  accent-color: var(--color-primary);
}

.funding-modal__option-label {
  grid-column: 2;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
}

.funding-modal__option-description {
  grid-column: 2;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.funding-modal__option-amount {
  grid-column: 3;
  grid-row: 1 / span 2;
  align-self: center;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.funding-modal__option-field {
  grid-column: 3;
  grid-row: 1 / span 2;
  align-self: center;
  width: 120px;
}

.funding-modal__preview {
  margin-top: var(--space-xs);
}

.funding-modal__preview-title {
  display: none;
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
}

.funding-modal__preview-helper {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.funding-modal__preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.funding-modal__preview-item {
  display: grid;
  gap: 2px;
}

.funding-modal__preview-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.funding-modal__preview-value {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.funding-modal__preview-value--error {
  color: var(--color-error);
}

.funding-modal__preview-value--positive {
  color: var(--color-positive);
}

.funding-modal__preview-value--negative {
  color: var(--color-error);
}

.funding-modal__warning {
  margin: 0;
  color: var(--color-error);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

@media (max-width: 560px) {
  .funding-modal__option {
    grid-template-columns: auto 1fr;
  }

  .funding-modal__option-amount,
  .funding-modal__option-field {
    grid-column: 2;
    grid-row: auto;
    justify-self: start;
  }

  .funding-modal__preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
