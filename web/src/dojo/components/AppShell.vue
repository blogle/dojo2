<template>
  <main class="shell">
    <section class="panel">
      <slot />
    </section>
  </main>
</template>

<style scoped>
.shell {
  display: grid;
  min-height: 100vh;
  padding: 2rem;
  place-items: center;
}

.panel {
  width: min(100%, 44rem);
  border: 1px solid var(--dojo-border-brown);
  border-radius: 24px;
  padding: clamp(1.5rem, 4vw, 3rem);
  background: rgba(244, 241, 234, 0.88);
  box-shadow: 0 24px 60px rgba(36, 28, 21, 0.12);
  backdrop-filter: blur(6px);
}

@media (max-width: 640px) {
  .shell {
    padding: 1rem;
  }
}
</style>
