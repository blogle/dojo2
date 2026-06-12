<script setup lang="ts">
defineProps<{ title: string; summary?: Record<string, unknown> | null }>();
</script>

<template>
  <div class="preview">
    <h3>Import preview</h3>
    <p>{{ title }}</p>
    <pre v-if="summary">{{ JSON.stringify(summary, null, 2) }}</pre>
  </div>
</template>

<style scoped>
pre {
  white-space: pre-wrap;
  font-size: 0.8rem;
}
</style>
