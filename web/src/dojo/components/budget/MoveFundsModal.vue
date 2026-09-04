<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Category } from "../../types";
import { formatCurrency, parseMoneyInput } from "../../utils/currency";

import SelectField from "../forms/SelectField.vue";
import CurrencyField from "../forms/CurrencyField.vue";
import PreviewBox from "../feedback/PreviewBox.vue";
import FormModal from "../overlays/FormModal.vue";

const props = defineProps<{
  visible: boolean;
  categories: Category[];
}>();

const emit = defineEmits<{
  close: [];
  submit: [payload: { from: string; to: string; amountMinor: number }];
}>();

const fromCategoryId = ref("");
const toCategoryId = ref("");
const amountString = ref("");

const categoryOptions = computed(() =>
  props.categories
    .filter((c) => !c.is_hidden)
    .map((c) => ({
      value: c.category_id,
      label: `${c.name} (${formatCurrency(c.available_minor)})`,
    })),
);

const amountMinor = computed(() => parseMoneyInput(amountString.value) ?? 0);

const fromCategory = computed(() =>
  props.categories.find(
    (category) => category.category_id === fromCategoryId.value,
  ),
);

const toCategory = computed(() =>
  props.categories.find(
    (category) => category.category_id === toCategoryId.value,
  ),
);

const fromAfter = computed(
  () => (fromCategory.value?.available_minor ?? 0) - amountMinor.value,
);

const toAfter = computed(
  () => (toCategory.value?.available_minor ?? 0) + amountMinor.value,
);

const canSubmit = computed(
  () =>
    fromCategoryId.value !== "" &&
    toCategoryId.value !== "" &&
    fromCategoryId.value !== toCategoryId.value &&
    amountMinor.value > 0,
);

function handleSubmit() {
  if (!canSubmit.value) return;
  if (fromCategoryId.value === toCategoryId.value) return;
  emit("submit", {
    from: fromCategoryId.value,
    to: toCategoryId.value,
    amountMinor: amountMinor.value,
  });
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) return;
    fromCategoryId.value = "";
    toCategoryId.value = "";
    amountString.value = "";
  },
);
</script>

<template>
  <FormModal
    :visible="visible"
    title="Move funds between categories"
    submit-text="Move funds"
    :submit-disabled="!canSubmit"
    @submit="handleSubmit"
    @cancel="emit('close')"
    @close="emit('close')"
  >
    <SelectField
      v-model="fromCategoryId"
      label="From"
      :options="[{ value: '', label: 'Choose source...' }, ...categoryOptions]"
      helper="Funds will be removed from this category."
    />
    <SelectField
      v-model="toCategoryId"
      label="To"
      :options="[
        { value: '', label: 'Choose destination...' },
        ...categoryOptions,
      ]"
      helper="Funds will be added to this category."
    />
    <CurrencyField
      v-model="amountString"
      label="Amount"
      placeholder="0.00"
      helper="Enter amount in dollars."
    />
    <PreviewBox title="Preview">
      <div class="move-funds-modal__preview-grid">
        <div class="move-funds-modal__preview-item">
          <span class="move-funds-modal__preview-label">Amount moved</span>
          <span class="move-funds-modal__preview-value">{{
            formatCurrency(amountMinor)
          }}</span>
        </div>
        <div class="move-funds-modal__preview-item">
          <span class="move-funds-modal__preview-label">{{
            fromCategory?.name ?? "Source"
          }}</span>
          <span
            class="move-funds-modal__preview-value move-funds-modal__preview-value--negative"
          >
            {{ formatCurrency(fromCategory?.available_minor ?? 0) }} →
            {{ formatCurrency(fromAfter) }}
          </span>
        </div>
        <div class="move-funds-modal__preview-item">
          <span class="move-funds-modal__preview-label">{{
            toCategory?.name ?? "Destination"
          }}</span>
          <span
            class="move-funds-modal__preview-value move-funds-modal__preview-value--positive"
          >
            {{ formatCurrency(toCategory?.available_minor ?? 0) }} →
            {{ formatCurrency(toAfter) }}
          </span>
        </div>
      </div>
    </PreviewBox>
  </FormModal>
</template>

<style scoped>
.move-funds-modal__preview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.move-funds-modal__preview-item {
  display: grid;
  gap: 2px;
}

.move-funds-modal__preview-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.move-funds-modal__preview-value {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.move-funds-modal__preview-value--positive {
  color: var(--color-positive);
}

.move-funds-modal__preview-value--negative {
  color: var(--color-error);
}

@media (max-width: 560px) {
  .move-funds-modal__preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
