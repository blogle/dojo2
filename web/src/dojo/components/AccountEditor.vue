<script setup lang="ts">
import { reactive } from "vue";

const emit = defineEmits<{ submit: [payload: Record<string, unknown>] }>();

const form = reactive({
  name: "",
  account_class: "BUDGET",
  budget_account_type: "DEPOSIT",
  is_hidden: false,
  is_active: true,
  display_liability_positive: false,
});

function handleSubmit(): void {
  emit("submit", { ...form });
}
</script>

<template>
  <form class="editor" @submit.prevent="handleSubmit">
    <h3>Add account</h3>
    <label class="field"
      ><span>Name</span><input v-model="form.name" type="text"
    /></label>
    <label class="field">
      <span>Class</span>
      <select v-model="form.account_class">
        <option value="BUDGET">Budget</option>
        <option value="TRACKING_BALANCE">Tracking balance</option>
        <option value="TRACKING_POSITIONS">Tracking positions</option>
        <option value="TRACKING_DEBT">Tracking debt</option>
      </select>
    </label>
    <label class="field" v-if="form.account_class === 'BUDGET'">
      <span>Budget type</span>
      <select v-model="form.budget_account_type">
        <option value="DEPOSIT">Deposit</option>
        <option value="CREDIT_CARD">Credit card</option>
      </select>
    </label>
    <label class="toggle"
      ><input v-model="form.is_hidden" type="checkbox" />Hidden</label
    >
    <label class="toggle"
      ><input v-model="form.is_active" type="checkbox" />Active</label
    >
    <label class="toggle" v-if="form.budget_account_type === 'CREDIT_CARD'"
      ><input
        v-model="form.display_liability_positive"
        type="checkbox"
      />Display liability as positive</label
    >
    <button type="submit">Save account</button>
  </form>
</template>

<style scoped>
.editor {
  display: grid;
  gap: 0.5rem;
}

h3 {
  margin: 0;
}
</style>
