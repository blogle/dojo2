<script setup lang="ts">
import { reactive, watch } from "vue";

import type { Account, Category, Transaction } from "../types";
import AccountSelect from "./AccountSelect.vue";
import CategoryOrSystemSelect from "./CategoryOrSystemSelect.vue";
import MoneyInput from "./MoneyInput.vue";

const props = defineProps<{
  accounts: Account[];
  categories: Category[];
  showHidden: boolean;
  editingTransaction?: Transaction | null;
}>();

const emit = defineEmits<{
  submit: [
    payload: {
      date: string;
      account_id: string;
      amount_minor: number;
      category_id: string | null;
      system_category: string | null;
      status: "PENDING" | "CLEARED";
      memo: string;
    },
  ];
}>();

const form = reactive({
  date: new Date().toISOString().slice(0, 10),
  account_id: "",
  amount_minor: null as number | null,
  category_id: "",
  system_category: "",
  useSystemCategory: false,
  status: "CLEARED" as "PENDING" | "CLEARED",
  memo: "",
});

watch(
  () => props.editingTransaction,
  (transaction) => {
    if (!transaction) {
      return;
    }
    form.date = transaction.date;
    form.account_id = transaction.account_id;
    form.amount_minor = transaction.amount_minor;
    form.category_id = transaction.category_id ?? "";
    form.system_category = transaction.system_category ?? "";
    form.useSystemCategory = Boolean(transaction.system_category);
    form.status = transaction.status;
    form.memo = transaction.memo;
  },
  { immediate: true },
);

function handleSubmit(): void {
  if (!form.account_id || form.amount_minor === null) {
    return;
  }
  emit("submit", {
    date: form.date,
    account_id: form.account_id,
    amount_minor: form.amount_minor,
    category_id: form.useSystemCategory ? null : form.category_id || null,
    system_category: form.useSystemCategory
      ? form.system_category || null
      : null,
    status: form.status,
    memo: form.memo,
  });
}
</script>

<template>
  <form class="transaction-entry-bar" @submit.prevent="handleSubmit">
    <label class="field">
      <span>Date</span>
      <input v-model="form.date" type="date" />
    </label>
    <AccountSelect v-model="form.account_id" :accounts="accounts" />
    <MoneyInput v-model="form.amount_minor" label="Amount" />
    <CategoryOrSystemSelect
      :categories="categories"
      :category-id="form.category_id"
      :show-hidden="showHidden"
      :system-category="form.system_category"
      :use-system-category="form.useSystemCategory"
      @update:category-id="form.category_id = $event"
      @update:system-category="form.system_category = $event"
      @update:use-system-category="form.useSystemCategory = $event"
    />
    <label class="field">
      <span>Status</span>
      <select v-model="form.status">
        <option value="CLEARED">Cleared</option>
        <option value="PENDING">Pending</option>
      </select>
    </label>
    <label class="field memo-field">
      <span>Memo</span>
      <input v-model="form.memo" type="text" />
    </label>
    <button type="submit">
      {{ editingTransaction ? "Save transaction" : "Add transaction" }}
    </button>
  </form>
</template>

<style scoped>
.transaction-entry-bar {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr)) auto;
  gap: 0.75rem;
  align-items: end;
}

.memo-field {
  grid-column: span 2;
}

@media (max-width: 960px) {
  .transaction-entry-bar {
    grid-template-columns: 1fr;
  }

  .memo-field {
    grid-column: span 1;
  }
}
</style>
