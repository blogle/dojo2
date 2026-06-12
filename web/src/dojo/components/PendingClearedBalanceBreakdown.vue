<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";

defineProps<{ pendingMinor: number; clearedMinor: number }>();
</script>

<template>
  <div class="breakdown">
    <span>Pending {{ formatMoneyMinor(pendingMinor) }}</span>
    <span>Cleared {{ formatMoneyMinor(clearedMinor) }}</span>
  </div>
</template>

<style scoped>
.breakdown {
  display: flex;
  gap: 0.75rem;
  font-family: var(--dojo-mono-font);
  color: var(--dojo-text-muted-brown);
}
</style>
