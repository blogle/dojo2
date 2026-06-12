<script setup lang="ts">
defineProps<{ message: string }>();
</script>

<template>
  <div class="error-banner">{{ message }}</div>
</template>

<style scoped>
.error-banner {
  border: 1px solid var(--dojo-brown-negative);
  background: color-mix(in srgb, var(--dojo-brown-negative) 8%, white);
  color: var(--dojo-brown-negative);
  padding: 0.75rem 1rem;
}
</style>
