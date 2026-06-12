<script setup lang="ts">
import type { CategoryGroup } from "../types";
import CategoryBudgetRow from "./CategoryBudgetRow.vue";

defineProps<{
  group: CategoryGroup;
  month: string;
  allCategories: CategoryGroup["categories"];
}>();

const emit = defineEmits<{ submitAllocation: [payload: { date: string; amount_minor: number; memo: string; from_bucket_id: string; to_bucket_id: string; path: "/api/allocations/fund" | "/api/allocations/move" | "/api/allocations/return-to-atb" }] }>();
</script>

<template>
  <section class="group-panel">
    <header>
      <h2>{{ group.name }}</h2>
      <p>{{ group.categories.length }} categories</p>
    </header>
    <CategoryBudgetRow
      v-for="category in group.categories"
      :key="category.category_id"
      :categories="allCategories"
      :category="category"
      :month="month"
      @submit-allocation="emit('submitAllocation', $event)"
    />
  </section>
</template>

<style scoped>
.group-panel {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-off-white);
  padding: 1rem;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

h2,
p {
  margin: 0;
}
</style>
