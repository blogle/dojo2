<script setup lang="ts">
defineProps<{ message: string }>();
</script>

<template>
  <div class="empty-state">{{ message }}</div>
</template>

<style scoped>
.empty-state {
  border: 1px dashed var(--dojo-border-brown);
  padding: 1rem;
  color: var(--dojo-text-muted-brown);
}
</style>
