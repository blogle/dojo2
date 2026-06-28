<template>
  <main class="reset-shell">
    <div class="reset-card">
      <p class="eyebrow">dojo frontend reset</p>
      <h1>UI rebuild pending</h1>
      <p>
        The prototype pages and components have been removed. The frontend will be
        rebuilt incrementally against <code>SPEC.md</code>.
      </p>
    </div>
  </main>
</template>

<style scoped>
.reset-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem;
}

.reset-card {
  width: min(100%, 40rem);
  padding: 2rem;
  border: 1px solid var(--dojo-border-brown);
  background: rgba(255, 252, 245, 0.92);
  box-shadow: 0 1rem 2.5rem rgba(58, 44, 34, 0.08);
}

.eyebrow {
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dojo-text-muted-brown);
}

h1 {
  margin: 0 0 0.75rem;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.1;
}

p {
  margin: 0;
  max-width: 34rem;
}
</style>
