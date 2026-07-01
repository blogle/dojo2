<script setup lang="ts">
import { computed } from "vue";

import CurrencyField from "../forms/CurrencyField.vue";
import DatePicker from "../forms/DatePicker.vue";
import RadioGroup from "../forms/RadioGroup.vue";
import SelectField from "../forms/SelectField.vue";

const props = defineProps<{
  goalType: string | null;
  goalAmountMinor: number | null;
  goalFrequency: string | null;
  goalDueDate: string | null;
  monthlyFundingMinor: number;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:goalType": [value: string | null];
  "update:goalAmountMinor": [value: number | null];
  "update:goalFrequency": [value: string | null];
  "update:goalDueDate": [value: string | null];
}>();

const goalTypeOptions = [
  { value: "ONE_TIME", label: "One-time goal" },
  { value: "RECURRING", label: "Recurring goal" },
  { value: "DISCRETIONARY", label: "Discretionary goal" },
];

const frequencyOptions = [
  { value: "MONTHLY", label: "Monthly" },
  { value: "QUARTERLY", label: "Quarterly" },
  { value: "YEARLY", label: "Yearly" },
];

const goalType = computed({
  get: () => props.goalType ?? "",
  set: (val: string) => emit("update:goalType", val || null),
});

const goalAmount = computed({
  get: () => (props.goalAmountMinor != null ? String(props.goalAmountMinor / 100) : ""),
  set: (val: string) => {
    const num = parseFloat(val);
    emit("update:goalAmountMinor", isNaN(num) ? null : Math.round(num * 100));
  },
});

const goalFrequency = computed({
  get: () => props.goalFrequency ?? "MONTHLY",
  set: (val: string) => emit("update:goalFrequency", val || null),
});

const goalDueDate = computed({
  get: () => props.goalDueDate ?? "",
  set: (val: string) => emit("update:goalDueDate", val || null),
});

const monthlyFundingDisplay = computed(() => {
  const amount = props.monthlyFundingMinor / 100;
  return `$ ${amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
});
</script>

<template>
  <div class="goal-editor" data-cy="goal-editor-root">
    <div class="goal-editor__section">
      <p class="goal-editor__label">Goal</p>
      <p class="goal-editor__helper">Set a goal and schedule for this category.</p>
    </div>

    <div class="goal-editor__section">
      <p class="goal-editor__field-label">Goal type</p>
      <RadioGroup
        v-model="goalType"
        :options="goalTypeOptions"
        :disabled="disabled"
      />
    </div>

    <div v-if="goalType === 'ONE_TIME'" class="goal-editor__section">
      <div class="goal-editor__row">
        <CurrencyField
          :model-value="goalAmount"
          label="Goal amount"
          :disabled="disabled"
          @update:model-value="goalAmount = $event"
        />
        <DatePicker
          :model-value="goalDueDate"
          label="Goal date"
          :disabled="disabled"
          @update:model-value="goalDueDate = $event"
        />
      </div>
    </div>

    <div v-if="goalType === 'RECURRING'" class="goal-editor__section">
      <div class="goal-editor__row">
        <CurrencyField
          :model-value="goalAmount"
          label="Amount per occurrence"
          :disabled="disabled"
          @update:model-value="goalAmount = $event"
        />
        <SelectField
          :model-value="goalFrequency"
          label="Frequency"
          :options="frequencyOptions"
          :disabled="disabled"
          @update:model-value="goalFrequency = $event"
        />
      </div>
      <div class="goal-editor__row">
        <DatePicker
          :model-value="goalDueDate"
          label="Next due date"
          :disabled="disabled"
          @update:model-value="goalDueDate = $event"
        />
        <div class="goal-editor__derived">
          <p class="goal-editor__field-label">Monthly funding</p>
          <p class="goal-editor__derived-value">{{ monthlyFundingDisplay }}</p>
          <p class="goal-editor__derived-note">
            This is the amount that will be funded each month.
          </p>
        </div>
      </div>
    </div>

    <div v-if="goalType === 'DISCRETIONARY'" class="goal-editor__section">
      <CurrencyField
        :model-value="goalAmount"
        label="Monthly goal"
        :disabled="disabled"
        @update:model-value="goalAmount = $event"
      />
    </div>
  </div>
</template>

<style scoped>
.goal-editor {
  display: grid;
  gap: var(--space-lg);
}

.goal-editor__section {
  display: grid;
  gap: var(--space-sm);
}

.goal-editor__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

@media (max-width: 600px) {
  .goal-editor__row {
    grid-template-columns: 1fr;
  }
}

.goal-editor__label {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-label-lg-font-family);
  font-size: var(--text-label-lg-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-label-lg-line-height);
}

.goal-editor__field-label {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}

.goal-editor__helper {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.goal-editor__derived {
  display: grid;
  gap: 2px;
}

.goal-editor__derived-value {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.goal-editor__derived-note {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}
</style>
