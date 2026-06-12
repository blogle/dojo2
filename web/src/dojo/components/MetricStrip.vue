<script setup lang="ts">
defineProps<{
  items: Array<{ label: string; value: string }>;
}>();
</script>

<template>
  <div class="metric-strip">
    <article v-for="item in items" :key="item.label" class="metric-card">
      <p>{{ item.label }}</p>
      <strong>{{ item.value }}</strong>
    </article>
  </div>
</template>

<style scoped>
.metric-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: 0.75rem;
}

.metric-card {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-off-white);
  padding: 0.75rem;
}

p {
  margin: 0;
  color: var(--dojo-text-muted-brown);
  text-transform: uppercase;
  font-size: 0.75rem;
}

strong {
  display: block;
  margin-top: 0.25rem;
  font-family: var(--dojo-mono-font);
  font-size: 1.1rem;
}
</style>
