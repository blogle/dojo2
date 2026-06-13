<script setup lang="ts">
import { computed } from "vue";

import PageHeader from "../components/PageHeader.vue";
import Panel from "../components/Panel.vue";
import TransactionEntryBar from "../components/TransactionEntryBar.vue";
import TransferEntryDialog from "../components/TransferEntryDialog.vue";
import VirtualTransactionTable from "../components/VirtualTransactionTable.vue";
import { useAppState } from "../state/app";
import type { Transaction } from "../types";

const app = useAppState();

const pageStart = computed(() =>
  app.state.transactions.length === 0 ? 0 : app.state.transactionOffset + 1,
);
const pageEnd = computed(
  () => app.state.transactionOffset + app.state.transactions.length,
);

function beginEdit(transaction: Transaction): void {
  app.state.editingTransactionId = transaction.transaction_id;
}
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="Transactions"
      subtitle="Enter, edit, delete, and clear budget activity."
    />
    <Panel>
      <TransactionEntryBar
        :accounts="app.state.accounts"
        :categories="app.state.categories"
        :editing-transaction="
          app.state.transactions.find(
            (row) => row.transaction_id === app.state.editingTransactionId,
          ) ?? null
        "
        :show-hidden="app.state.showHidden"
        @submit="app.submitTransaction($event)"
      />
    </Panel>
    <Panel>
      <TransferEntryDialog
        :accounts="app.state.accounts"
        @submit="app.submitTransfer($event)"
      />
    </Panel>
    <Panel>
      <VirtualTransactionTable
        :key="app.state.transactionOffset"
        :transactions="app.state.transactions"
        @edit="beginEdit($event)"
        @remove="app.removeTransaction($event)"
        @toggle-status="app.toggleTransactionStatus($event)"
      />
      <div class="pagination-bar">
        <span class="page-summary">
          Showing {{ pageStart }}-{{ pageEnd }} of
          {{ app.state.transactionTotal }}
        </span>
        <div class="page-controls">
          <button
            class="btn btn-secondary"
            :disabled="app.state.loading || app.state.transactionOffset === 0"
            @click="app.loadPreviousTransactions()"
          >
            Previous
          </button>
          <button
            class="btn btn-secondary"
            :disabled="app.state.loading || !app.state.hasMoreTransactions"
            @click="app.loadMoreTransactions()"
          >
            {{ app.state.loading ? "Loading..." : "Next" }}
          </button>
        </div>
      </div>
    </Panel>
  </div>
</template>

<style scoped>
.page-grid {
  display: grid;
  gap: 1rem;
}
.pagination-bar {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 1rem;
}

.page-controls {
  display: flex;
  gap: 0.5rem;
}

.page-summary {
  font-size: 0.9rem;
}

@media (max-width: 720px) {
  .pagination-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .page-controls {
    justify-content: space-between;
  }
}
</style>
