<script setup lang="ts">
import { RouterLink } from "vue-router";

defineProps<{
  ready: boolean;
}>();
</script>

<template>
  <nav class="top-nav">
    <RouterLink class="brand" to="/budget">dojo</RouterLink>
    <div v-if="ready" class="links">
      <RouterLink to="/budget">Budget</RouterLink>
      <RouterLink to="/transactions">Transactions</RouterLink>
      <RouterLink to="/accounts">Accounts</RouterLink>
      <RouterLink to="/categories">Categories</RouterLink>
      <RouterLink to="/net-worth">Net Worth</RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.top-nav {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--dojo-border-brown);
  padding-bottom: 0.75rem;
}

.brand,
.links a {
  text-decoration: none;
  color: var(--dojo-text-dark-brown);
  font-weight: 700;
}

.links {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.router-link-active {
  color: var(--dojo-green-dark);
}
</style>
