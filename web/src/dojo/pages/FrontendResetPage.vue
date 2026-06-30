<template>
  <main class="reset-shell">
    <div class="reset-card">
      <p class="eyebrow">dojo frontend reset</p>
      <h1>UI rebuild pending</h1>
      <p>
        The product pages will be rebuilt incrementally against
        <code>SPEC.md</code> using the shared design-system catalog.
      </p>
      <p v-if="isDev" class="hint">
        Open <code>/dev/design-system</code> locally to inspect the current
        foundations and layout primitives.
      </p>
    </div>
  </main>
</template>

<script setup lang="ts">
const isDev = import.meta.env.DEV;
</script>

<style scoped>
.reset-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--space-xl);
}

.reset-card {
  width: min(100%, 40rem);
  padding: var(--space-xl);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
}

.eyebrow,
.hint {
  color: var(--color-on-surface-muted);
}

.eyebrow {
  margin: 0 0 var(--space-sm);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

h1 {
  margin: 0 0 var(--space-sm);
  color: var(--color-on-surface);
  font-family: var(--text-display-lg-font-family);
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: var(--text-display-lg-font-weight);
  line-height: var(--text-display-lg-line-height);
  letter-spacing: var(--text-display-lg-letter-spacing);
}

p {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.hint {
  margin-top: var(--space-sm);
}
</style>
