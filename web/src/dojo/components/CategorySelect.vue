<script setup lang="ts">
import { computed } from "vue";

import type { Category } from "../types";

const props = defineProps<{
  modelValue: string;
  categories: Category[];
  showHidden?: boolean;
}>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const visibleCategories = computed(() =>
  props.categories.filter(
    (category) => props.showHidden || !category.is_hidden,
  ),
);
</script>

<template>
  <label class="field">
    <span>Category</span>
    <select
      :value="modelValue"
      @change="
        emit('update:modelValue', ($event.target as HTMLSelectElement).value)
      "
    >
      <option value="">Select category</option>
      <option
        v-for="category in visibleCategories"
        :key="category.category_id"
        :value="category.category_id"
      >
        {{ category.group_name }} / {{ category.name }}
      </option>
    </select>
  </label>
</template>
