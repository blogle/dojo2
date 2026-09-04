<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Category, CategoryGroup } from "../../types";
import { formatCurrency, parseMoneyInput } from "../../utils/currency";

import CurrencyField from "../forms/CurrencyField.vue";
import FormModal from "../overlays/FormModal.vue";

const props = defineProps<{
  visible: boolean;
  group: CategoryGroup | null;
  categories: Category[];
}>();

const emit = defineEmits<{
  close: [];
  submit: [payload: Array<{ categoryId: string; monthlyGoalMinor: number }>];
}>();

const fundingAmounts = ref<Record<string, string>>({});

watch(
  () => props.group,
  (g) => {
    if (!g) return;
    const amounts: Record<string, string> = {};
    for (const cat of g.categories) {
      amounts[cat.category_id] = "";
    }
    fundingAmounts.value = amounts;
  },
);

const groupCategories = computed(() => {
  if (!props.group) return [];
  return props.categories.filter(
    (c) => c.group_id === props.group!.group_id && !c.is_hidden,
  );
});

const totalFunding = computed(() => {
  return Object.values(fundingAmounts.value).reduce(
    (sum, v) => sum + (parseMoneyInput(v) ?? 0),
    0,
  );
});

function handleSubmit() {
  const entries = Object.entries(fundingAmounts.value)
    .map(([categoryId, v]) => ({
      categoryId,
      monthlyGoalMinor: parseMoneyInput(v) ?? 0,
    }))
    .filter((e) => e.monthlyGoalMinor > 0);
  if (entries.length === 0) return;
  emit("submit", entries);
}
</script>

<template>
  <FormModal
    :visible="visible"
    :title="`Fund: ${group?.name ?? ''}`"
    submit-text="Submit funding"
    @submit="handleSubmit"
    @cancel="emit('close')"
    @close="emit('close')"
  >
    <div
      v-if="groupCategories.length === 0"
      style="color: var(--color-on-surface-muted)"
    >
      No categories in this group.
    </div>
    <div v-else style="display: grid; gap: var(--space-md)">
      <div
        v-for="cat in groupCategories"
        :key="cat.category_id"
        style="display: grid; gap: var(--space-xs)"
      >
        <CurrencyField
          :model-value="fundingAmounts[cat.category_id] ?? ''"
          :label="cat.name"
          placeholder="0.00"
          :helper="`Available: ${formatCurrency(cat.available_minor)}`"
          @update:model-value="fundingAmounts[cat.category_id] = $event"
        />
      </div>
      <div
        style="
          padding: var(--space-sm);
          background: var(--color-surface-muted);
          text-align: right;
        "
      >
        Total: {{ formatCurrency(totalFunding) }}
      </div>
    </div>
  </FormModal>
</template>
