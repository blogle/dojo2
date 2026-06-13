<script setup lang="ts">
import { reactive } from "vue";

import type { Account } from "../types";
import AccountSelect from "./AccountSelect.vue";
import MoneyInput from "./MoneyInput.vue";

defineProps<{ accounts: Account[] }>();
const emit = defineEmits<{
  submit: [
    payload: {
      date: string;
      from_account_id: string;
      to_account_id: string;
      amount_minor: number;
      status: "PENDING" | "CLEARED";
      memo: string;
    },
  ];
}>();

const form = reactive({
  date: new Date().toISOString().slice(0, 10),
  from_account_id: "",
  to_account_id: "",
  amount_minor: null as number | null,
  status: "CLEARED" as "PENDING" | "CLEARED",
  memo: "",
});

function handleSubmit(): void {
  if (
    !form.from_account_id ||
    !form.to_account_id ||
    form.amount_minor === null
  ) {
    return;
  }
  emit("submit", {
    date: form.date,
    from_account_id: form.from_account_id,
    to_account_id: form.to_account_id,
    amount_minor: form.amount_minor,
    status: form.status,
    memo: form.memo,
  });
}
</script>

<template>
  <form class="transfer-form" @submit.prevent="handleSubmit">
    <h3>Transfer helper</h3>
    <label class="field">
      <span>Date</span>
      <input v-model="form.date" type="date" />
    </label>
    <AccountSelect v-model="form.from_account_id" :accounts="accounts" />
    <AccountSelect v-model="form.to_account_id" :accounts="accounts" />
    <MoneyInput v-model="form.amount_minor" label="Amount" />
    <label class="field">
      <span>Status</span>
      <select v-model="form.status">
        <option value="CLEARED">Cleared</option>
        <option value="PENDING">Pending</option>
      </select>
    </label>
    <label class="field">
      <span>Memo</span>
      <input v-model="form.memo" type="text" />
    </label>
    <button type="submit">Create transfer</button>
  </form>
</template>

<style scoped>
.transfer-form {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr)) auto;
  gap: 0.75rem;
  align-items: end;
}

h3 {
  grid-column: 1 / -1;
  margin: 0;
}

@media (max-width: 960px) {
  .transfer-form {
    grid-template-columns: 1fr;
  }
}
</style>
