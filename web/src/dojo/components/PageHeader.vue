<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <header class="page-header">
    <div>
      <p class="eyebrow">local-first envelope budget</p>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <slot />
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
}

.eyebrow,
.subtitle {
  margin: 0;
  color: var(--dojo-text-muted-brown);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.75rem;
  font-weight: 700;
}

h1 {
  margin: 0.25rem 0 0;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
}
</style>
