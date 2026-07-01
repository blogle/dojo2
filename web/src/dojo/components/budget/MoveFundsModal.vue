<script setup lang="ts">
import { computed, ref } from "vue";

import type { Category } from "../../types";
import { formatCurrency } from "../../utils/currency";

import SelectField from "../forms/SelectField.vue";
import CurrencyField from "../forms/CurrencyField.vue";
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

function handleSubmit() {
  const amountMinor = Math.round(parseFloat(amountString.value || "0") * 100);
  if (!fromCategoryId.value || !toCategoryId.value || amountMinor <= 0) return;
  if (fromCategoryId.value === toCategoryId.value) return;
  emit("submit", {
    from: fromCategoryId.value,
    to: toCategoryId.value,
    amountMinor,
  });
  fromCategoryId.value = "";
  toCategoryId.value = "";
  amountString.value = "";
}
</script>

<template>
  <FormModal
    :visible="visible"
    title="Move funds between categories"
    submit-text="Move funds"
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
      :options="[{ value: '', label: 'Choose destination...' }, ...categoryOptions]"
      helper="Funds will be added to this category."
    />
    <CurrencyField
      v-model="amountString"
      label="Amount"
      placeholder="0.00"
      helper="Enter amount in dollars."
    />
  </FormModal>
</template>
