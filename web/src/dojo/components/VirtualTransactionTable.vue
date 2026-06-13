<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";
import type { Transaction } from "../types";
import TransactionStatusToggle from "./TransactionStatusToggle.vue";
import VirtualDataTable from "./VirtualDataTable.vue";

defineProps<{
  transactions: Transaction[];
}>();

const emit = defineEmits<{
  edit: [transaction: Transaction];
  remove: [transactionId: string];
  toggleStatus: [transaction: Transaction];
}>();
</script>

<template>
  <div class="transaction-table">
    <header class="table-head">
      <span>Date</span>
      <span>Account</span>
      <span>Category</span>
      <span>Memo</span>
      <span class="money">Amount</span>
      <span>Status</span>
      <span>Actions</span>
    </header>
    <VirtualDataTable
      :items="transactions"
      :row-height="50"
      :viewport-height="420"
    >
      <template #default="slotProps">
        <div
          v-for="transaction in slotProps.items"
          :key="transaction.transaction_id"
          class="table-row"
          :data-transaction-id="transaction.transaction_id"
        >
          <span>{{ transaction.date }}</span>
          <span>{{ transaction.account_name }}</span>
          <span>{{
            transaction.category_name ?? transaction.system_category
          }}</span>
          <span>{{ transaction.memo }}</span>
          <span class="money">{{
            formatMoneyMinor(transaction.amount_minor)
          }}</span>
          <TransactionStatusToggle
            :status="transaction.status"
            @toggle="emit('toggleStatus', transaction)"
          />
          <span class="actions">
            <button type="button" @click="emit('edit', transaction)">
              Edit
            </button>
            <button
              type="button"
              @click="emit('remove', transaction.transaction_id)"
            >
              Delete
            </button>
          </span>
        </div>
      </template>
    </VirtualDataTable>
  </div>
</template>

<style scoped>
.transaction-table {
  display: grid;
  gap: 0.25rem;
}

.table-head,
.table-row {
  display: grid;
  grid-template-columns: 7rem 1fr 1fr 1fr 8rem 7rem 8rem;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem 0.75rem;
}

.table-head {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-muted-sand);
  text-transform: uppercase;
  font-size: 0.75rem;
}

.table-row {
  border-bottom: 1px solid var(--dojo-border-tan);
  min-height: 50px;
}

.money {
  font-family: var(--dojo-mono-font);
  text-align: right;
}

.actions {
  display: flex;
  gap: 0.25rem;
}

@media (max-width: 960px) {
  .table-head,
  .table-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
