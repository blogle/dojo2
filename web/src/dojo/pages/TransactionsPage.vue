<script setup lang="ts">
import PageHeader from "../components/PageHeader.vue";
import Panel from "../components/Panel.vue";
import TransactionEntryBar from "../components/TransactionEntryBar.vue";
import TransferEntryDialog from "../components/TransferEntryDialog.vue";
import VirtualTransactionTable from "../components/VirtualTransactionTable.vue";
import { useAppState } from "../state/app";
import type { Transaction } from "../types";

const app = useAppState();

function beginEdit(transaction: Transaction): void {
  app.state.editingTransactionId = transaction.transaction_id;
}
</script>

<template>
  <div class="page-grid">
    <PageHeader title="Transactions" subtitle="Enter, edit, delete, and clear budget activity." />
    <Panel>
      <TransactionEntryBar
        :accounts="app.state.accounts"
        :categories="app.state.categories"
        :editing-transaction="app.state.transactions.find((row) => row.transaction_id === app.state.editingTransactionId) ?? null"
        :show-hidden="app.state.showHidden"
        @submit="app.submitTransaction($event)"
      />
    </Panel>
    <Panel>
      <TransferEntryDialog :accounts="app.state.accounts" @submit="app.submitTransfer($event)" />
    </Panel>
    <Panel>
      <VirtualTransactionTable
        :transactions="app.state.transactions"
        @edit="beginEdit($event)"
        @remove="app.removeTransaction($event)"
        @toggle-status="app.toggleTransactionStatus($event)"
      />
    </Panel>
  </div>
</template>

<style scoped>
.page-grid {
  display: grid;
  gap: 1rem;
}
</style>
