<script setup lang="ts">
import AccountDetailPanel from "../components/AccountDetailPanel.vue";
import AccountEditor from "../components/AccountEditor.vue";
import AccountList from "../components/AccountList.vue";
import HiddenEntitiesToggle from "../components/HiddenEntitiesToggle.vue";
import PageHeader from "../components/PageHeader.vue";
import Panel from "../components/Panel.vue";
import { useAppState } from "../state/app";

const app = useAppState();
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="Accounts"
      subtitle="Track balances, hidden entities, and credit card liabilities."
    />
    <div class="toolbar">
      <HiddenEntitiesToggle
        :model-value="app.state.showHidden"
        @update:model-value="app.setShowHidden($event)"
      />
    </div>
    <Panel><AccountEditor @submit="app.saveAccount($event)" /></Panel>
    <AccountList :accounts="app.state.accounts" />
    <Panel>
      <AccountDetailPanel
        :accounts="app.state.accounts"
        :transactions="app.state.transactions"
        @edit="app.state.editingTransactionId = $event.transaction_id"
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

.toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
