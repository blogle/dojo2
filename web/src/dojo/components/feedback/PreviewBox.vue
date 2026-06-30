<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
  }>(),
  {
    title: undefined,
  },
);
</script>

<template>
  <div class="preview-box" data-cy="preview-box-root">
    <span v-if="title" class="preview-box__title">{{ title }}</span>
    <slot />
  </div>
</template>

<style scoped>
.preview-box {
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  border-radius: var(--radius-all);
  padding: var(--space-md);
  display: grid;
  gap: var(--space-sm);
}

.preview-box__title {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}
</style>
