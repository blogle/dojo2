<script setup lang="ts">
import { computed, ref } from "vue";

import type { Category } from "../types";
import MoneyInput from "./MoneyInput.vue";

const props = defineProps<{
  category: Category;
  categories: Category[];
  month: string;
}>();

const emit = defineEmits<{
  submit: [
    payload: {
      date: string;
      amount_minor: number;
      memo: string;
      from_bucket_id: string;
      to_bucket_id: string;
      path:
        | "/api/allocations/fund"
        | "/api/allocations/move"
        | "/api/allocations/return-to-atb";
    },
  ];
}>();

const mode = ref<"fund" | "move" | "return">("fund");
const amountMinor = ref<number | null>(null);
const targetCategoryId = ref("");

const destinationOptions = computed(() =>
  props.categories.filter(
    (category) => category.category_id !== props.category.category_id,
  ),
);

function handleSubmit(): void {
  if (amountMinor.value === null || amountMinor.value <= 0) {
    return;
  }
  const payload = {
    date: `${props.month}-01`,
    amount_minor: amountMinor.value,
    memo: `${mode.value} ${props.category.name}`,
    from_bucket_id:
      mode.value === "fund"
        ? "00000000-0000-0000-0000-00000000a7b0"
        : props.category.bucket_id,
    to_bucket_id:
      mode.value === "fund"
        ? props.category.bucket_id
        : mode.value === "move"
          ? (destinationOptions.value.find(
              (category) => category.category_id === targetCategoryId.value,
            )?.bucket_id ?? "")
          : "00000000-0000-0000-0000-00000000a7b0",
    path:
      mode.value === "fund"
        ? "/api/allocations/fund"
        : mode.value === "move"
          ? "/api/allocations/move"
          : "/api/allocations/return-to-atb",
  } as const;
  emit("submit", payload);
}
</script>

<template>
  <div class="allocation-popover">
    <div class="modes">
      <button type="button" @click="mode = 'fund'">Fund</button>
      <button type="button" @click="mode = 'move'">Move</button>
      <button type="button" @click="mode = 'return'">Return</button>
    </div>
    <MoneyInput v-model="amountMinor" label="Amount" />
    <label v-if="mode === 'move'" class="field">
      <span>To category</span>
      <select v-model="targetCategoryId">
        <option value="">Select category</option>
        <option
          v-for="category in destinationOptions"
          :key="category.category_id"
          :value="category.category_id"
        >
          {{ category.name }}
        </option>
      </select>
    </label>
    <button type="button" @click="handleSubmit">Submit</button>
  </div>
</template>

<style scoped>
.allocation-popover {
  display: grid;
  gap: 0.5rem;
  padding-top: 0.5rem;
}

.modes {
  display: flex;
  gap: 0.25rem;
}
</style>
