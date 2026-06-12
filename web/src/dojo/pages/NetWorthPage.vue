<script setup lang="ts">
import PageHeader from "../components/PageHeader.vue";
import Panel from "../components/Panel.vue";
import { formatMoneyMinor } from "../lib/money";
import { useAppState } from "../state/app";

const app = useAppState();
</script>

<template>
  <div class="page-grid">
    <PageHeader title="Net Worth" subtitle="Current net worth includes hidden accounts. Budget accounts come from the ledger; duplicated imported budget valuations are listed but ignored in the total." />
    <Panel>
      <p class="eyebrow">Current net worth</p>
      <h2>{{ formatMoneyMinor(app.state.netWorth?.current_net_worth_minor ?? 0) }}</h2>
    </Panel>
    <Panel>
      <table class="net-worth-table">
        <thead>
          <tr>
            <th>Account</th>
            <th>Source</th>
            <th>Amount</th>
            <th>Ignored</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in app.state.netWorth?.items ?? []" :key="`${item.account_name}-${item.source}`">
            <td>{{ item.account_name }}</td>
            <td>
              {{ item.source === "ledger"
                ? "Ledger balance"
                : item.ignored_reason === "ambiguous_budget_duplicate"
                  ? "Imported valuation (ambiguous duplicate, ignored)"
                  : item.ignored_import_value
                    ? "Imported valuation (ignored in total)"
                    : "Imported valuation" }}
            </td>
            <td>{{ formatMoneyMinor(item.net_worth_minor) }}</td>
            <td>{{ item.ignored_import_value ? "yes" : "no" }}</td>
          </tr>
        </tbody>
      </table>
    </Panel>
  </div>
</template>

<style scoped>
.page-grid {
  display: grid;
  gap: 1rem;
}

h2 {
  margin: 0;
  font-family: var(--dojo-mono-font);
}

.eyebrow {
  margin: 0 0 0.25rem;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.net-worth-table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid var(--dojo-border-tan);
  padding: 0.5rem;
}
</style>
