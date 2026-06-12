<script setup lang="ts">
import { reactive } from "vue";

const emit = defineEmits<{ submit: [payload: Record<string, unknown>] }>();
const form = reactive({ name: "", sort_order: 100, is_hidden: false });
</script>

<template>
  <form class="editor" @submit.prevent="emit('submit', { ...form })">
    <h3>Add group</h3>
    <label class="field"><span>Name</span><input v-model="form.name" type="text" /></label>
    <label class="field"><span>Sort order</span><input v-model.number="form.sort_order" type="number" /></label>
    <label class="toggle"><input v-model="form.is_hidden" type="checkbox" />Hidden</label>
    <button type="submit">Save group</button>
  </form>
</template>

<style scoped>
.editor {
  display: grid;
  gap: 0.5rem;
}
</style>
