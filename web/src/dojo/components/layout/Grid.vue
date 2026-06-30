<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    columns?: string;
    gap?: string;
    tag?: string;
  }>(),
  {
    columns: "repeat(3, minmax(0, 1fr))",
    gap: "var(--space-sm)",
    tag: "div",
  },
);

const style = computed(() => ({
  gridTemplateColumns: props.columns,
  gap: props.gap,
}));
</script>

<template>
  <component :is="tag" class="grid" :style="style" data-cy="grid-root">
    <slot />
  </component>
</template>

<style scoped>
.grid {
  display: grid;
}
</style>
