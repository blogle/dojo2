<script setup lang="ts">
import { computed, ref } from "vue";

import type { Category } from "../../types";
import { formatCurrency } from "../../utils/currency";

import CurrencyField from "../forms/CurrencyField.vue";
import FormModal from "../overlays/FormModal.vue";

const props = defineProps<{
  visible: boolean;
  category: Category | null;
}>();

const emit = defineEmits<{
  close: [];
  submit: [payload: { categoryId: string; amountMinor: number }];
}>();

type FundingOption = "next-month" | "monthly-goal" | "custom";

const selectedOption = ref<FundingOption>("next-month");
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

const selectedAmount = computed(() => {
  if (selectedOption.value === "next-month") return fundUpToNextMonth.value;
  if (selectedOption.value === "monthly-goal") return fundToMonthlyGoal.value;
  return Math.round(parseFloat(customAmount.value || "0") * 100);
});

const currentAvailable = computed(() => props.category?.available_minor ?? 0);
const newAvailable = computed(
  () => currentAvailable.value + selectedAmount.value,
);
const currentAtb = computed(() => {
  const budget = (
    window as unknown as { __budget?: { available_to_budget_minor: number } }
  ).__budget;
  return budget?.available_to_budget_minor ?? 0;
});
const newAtb = computed(() => currentAtb.value - selectedAmount.value);
const willBeNegative = computed(() => newAtb.value < 0);

const optionItems = computed(() => [
  {
    key: "next-month" as const,
    label: "Fund up to next month",
    amount: fundUpToNextMonth.value,
  },
  {
    key: "monthly-goal" as const,
    label: "Fund to monthly goal",
    amount: fundToMonthlyGoal.value,
  },
]);

function handleSubmit() {
  if (!props.category || selectedAmount.value <= 0) return;
  emit("submit", {
    categoryId: props.category.category_id,
    amountMinor: selectedAmount.value,
  });
  selectedOption.value = "next-month";
  customAmount.value = "";
}
</script>

<template>
  <FormModal
    :visible="visible"
    :title="`Fund: ${category?.name ?? ''}`"
    submit-text="Save"
    :submit-disabled="selectedAmount <= 0"
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
      <p class="funding-modal__field-label">Funding option</p>
      <div class="funding-modal__options">
        <label
          v-for="opt in optionItems"
          :key="opt.key"
          class="funding-modal__option"
          :class="{
            'funding-modal__option--selected': selectedOption === opt.key,
          }"
        >
          <input
            type="radio"
            :value="opt.key"
            v-model="selectedOption"
            class="funding-modal__radio"
          />
          <span class="funding-modal__option-label">{{ opt.label }}</span>
          <span class="funding-modal__option-amount">{{
            formatCurrency(opt.amount)
          }}</span>
        </label>
        <label
          class="funding-modal__option"
          :class="{
            'funding-modal__option--selected': selectedOption === 'custom',
          }"
        >
          <input
            type="radio"
            value="custom"
            v-model="selectedOption"
            class="funding-modal__radio"
          />
          <span class="funding-modal__option-label">Custom amount</span>
          <span class="funding-modal__option-field">
            <CurrencyField
              v-model="customAmount"
              placeholder="0.00"
              :disabled="selectedOption !== 'custom'"
            />
          </span>
        </label>
      </div>
    </div>

    <div class="funding-modal__preview">
      <p class="funding-modal__preview-title">Preview</p>
      <p class="funding-modal__preview-helper">
        Review the results of this action before you save.
      </p>
      <div class="funding-modal__preview-grid">
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label">Amount being funded</span>
          <span class="funding-modal__preview-value">{{
            formatCurrency(selectedAmount)
          }}</span>
        </div>
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label"
            >{{ category?.name }} balance</span
          >
          <span class="funding-modal__preview-value">
            {{ formatCurrency(currentAvailable) }} →
            {{ formatCurrency(newAvailable) }}
          </span>
        </div>
        <div class="funding-modal__preview-item">
          <span class="funding-modal__preview-label">Available to budget</span>
          <span
            class="funding-modal__preview-value"
            :class="{ 'funding-modal__preview-value--error': willBeNegative }"
          >
            {{ formatCurrency(currentAtb) }} → {{ formatCurrency(newAtb) }}
          </span>
        </div>
      </div>
      <p v-if="willBeNegative" class="funding-modal__warning">
        Available to budget will be negative after this action.
      </p>
    </div>
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
  display: flex;
  align-items: center;
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
  flex: 1;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

.funding-modal__option-amount {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.funding-modal__option-field {
  width: 120px;
}

.funding-modal__preview {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  padding: var(--space-md);
  display: grid;
  gap: var(--space-sm);
}

.funding-modal__preview-title {
  margin: 0;
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

.funding-modal__warning {
  margin: 0;
  color: var(--color-error);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}
</style>
