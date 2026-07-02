<script setup lang="ts">
defineProps<{
  title: string;
  body: string;
  eyebrow?: string;
}>();
</script>

<template>
  <section class="intro-callout" data-cy="intro-callout-root">
    <p v-if="eyebrow" class="intro-callout__eyebrow">{{ eyebrow }}</p>
    <h2 class="intro-callout__title">{{ title }}</h2>
    <p class="intro-callout__body">{{ body }}</p>
  </section>
</template>

<style scoped>
.intro-callout {
  border: 1px solid var(--color-outline);
  background: color-mix(
    in srgb,
    var(--color-surface) 78%,
    var(--color-surface-muted)
  );
  padding: var(--layout-intro-padding);
}

.intro-callout__eyebrow {
  margin: 0 0 var(--space-xs);
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  line-height: var(--text-label-sm-line-height);
  text-transform: uppercase;
}

.intro-callout__title {
  margin: 0 0 var(--space-xs);
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.intro-callout__body {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}
</style>
