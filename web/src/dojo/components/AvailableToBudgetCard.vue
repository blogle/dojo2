<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";

defineProps<{ amountMinor: number }>();
</script>

<template>
  <article class="atb-card">
    <p>Available To Budget</p>
    <strong>{{ formatMoneyMinor(amountMinor) }}</strong>
  </article>
</template>

<style scoped>
.atb-card {
  border: 1px solid var(--dojo-green-dark);
  background: var(--dojo-green-pale);
  padding: 1rem;
}

p {
  margin: 0;
  text-transform: uppercase;
  font-size: 0.75rem;
  color: var(--dojo-green-dark);
}

strong {
  display: block;
  margin-top: 0.25rem;
  font-family: var(--dojo-mono-font);
  font-size: 1.3rem;
}
</style>
