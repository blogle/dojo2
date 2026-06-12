<script setup lang="ts">
import { reactive } from "vue";

import type { CategoryGroup } from "../types";

defineProps<{ groups: CategoryGroup[] }>();
const emit = defineEmits<{ submit: [payload: Record<string, unknown>] }>();

const form = reactive({
  group_id: "",
  name: "",
  sort_order: 100,
  is_hidden: false,
  is_active: true,
  target_amount_minor: 0,
  due_date_rule: "",
});
</script>

<template>
  <form class="editor" @submit.prevent="emit('submit', { ...form })">
    <h3>Add category</h3>
    <label class="field">
      <span>Group</span>
      <select v-model="form.group_id">
        <option value="">Select group</option>
        <option v-for="group in groups" :key="group.group_id" :value="group.group_id">{{ group.name }}</option>
      </select>
    </label>
    <label class="field"><span>Name</span><input v-model="form.name" type="text" /></label>
    <label class="field"><span>Sort order</span><input v-model.number="form.sort_order" type="number" /></label>
    <label class="field"><span>Target minor</span><input v-model.number="form.target_amount_minor" type="number" /></label>
    <label class="field"><span>Due rule</span><input v-model="form.due_date_rule" type="text" /></label>
    <label class="toggle"><input v-model="form.is_hidden" type="checkbox" />Hidden</label>
    <label class="toggle"><input v-model="form.is_active" type="checkbox" />Active</label>
    <button type="submit">Save category</button>
  </form>
</template>

<style scoped>
.editor {
  display: grid;
  gap: 0.5rem;
}
</style>
