<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";
import type { Account } from "../types";
import PendingClearedBalanceBreakdown from "./PendingClearedBalanceBreakdown.vue";

defineProps<{ account: Account }>();
</script>

<template>
  <article class="account-card">
    <div>
      <h3>{{ account.name }}</h3>
      <p>{{ account.account_class }}<span v-if="account.is_hidden"> · hidden</span></p>
    </div>
    <strong>{{ formatMoneyMinor(account.display_balance_minor) }}</strong>
    <PendingClearedBalanceBreakdown :cleared-minor="account.cleared_balance_minor" :pending-minor="account.pending_balance_minor" />
  </article>
</template>

<style scoped>
.account-card {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-off-white);
  padding: 1rem;
  display: grid;
  gap: 0.5rem;
}

h3,
p {
  margin: 0;
}

strong {
  font-family: var(--dojo-mono-font);
  font-size: 1.1rem;
}
</style>
