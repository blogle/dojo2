<template>
  <section class="panel">
    <slot />
  </section>
</template>

<style scoped>
.panel {
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-warm-paper);
  padding: 1rem;
}
</style>
