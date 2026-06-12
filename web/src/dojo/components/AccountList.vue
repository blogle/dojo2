<script setup lang="ts">
import type { Account } from "../types";
import AccountBalanceCard from "./AccountBalanceCard.vue";

defineProps<{ accounts: Account[] }>();
</script>

<template>
  <div class="account-list">
    <AccountBalanceCard v-for="account in accounts" :key="account.account_id" :account="account" />
  </div>
</template>

<style scoped>
.account-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 0.75rem;
}
</style>
