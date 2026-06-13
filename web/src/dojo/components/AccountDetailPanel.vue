<script setup lang="ts">
import { computed, ref } from "vue";

import type { Account, Transaction } from "../types";
import EmptyState from "./EmptyState.vue";
import VirtualTransactionTable from "./VirtualTransactionTable.vue";

const props = defineProps<{
  accounts: Account[];
  transactions: Transaction[];
}>();

const emit = defineEmits<{
  edit: [transaction: Transaction];
  remove: [transactionId: string];
  toggleStatus: [transaction: Transaction];
}>();

const selectedAccountId = ref("");
const selectedAccount = computed(
  () =>
    props.accounts.find(
      (account) => account.account_id === selectedAccountId.value,
    ) ??
    props.accounts[0] ??
    null,
);
const accountTransactions = computed(() =>
  props.transactions.filter(
    (transaction) =>
      transaction.account_id === selectedAccount.value?.account_id,
  ),
);
</script>

<template>
  <section class="account-detail">
    <label class="field">
      <span>Account detail</span>
      <select v-model="selectedAccountId">
        <option
          v-for="account in accounts"
          :key="account.account_id"
          :value="account.account_id"
        >
          {{ account.name }}
        </option>
      </select>
    </label>
    <EmptyState v-if="!selectedAccount" message="No account selected." />
    <VirtualTransactionTable
      v-else
      :transactions="accountTransactions"
      @edit="emit('edit', $event)"
      @remove="emit('remove', $event)"
      @toggle-status="emit('toggleStatus', $event)"
    />
  </section>
</template>

<style scoped>
.account-detail {
  display: grid;
  gap: 0.75rem;
}
</style>
