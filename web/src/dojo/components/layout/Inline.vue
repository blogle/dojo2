<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    gap?: string;
    wrap?: boolean;
    align?: string;
    tag?: string;
  }>(),
  {
    gap: "var(--space-sm)",
    wrap: false,
    align: "center",
    tag: "div",
  },
);

const style = computed(() => ({
  gap: props.gap,
  alignItems: props.align,
  flexWrap: props.wrap ? "wrap" : "nowrap",
}));
</script>

<template>
  <component :is="tag" class="inline" :style="style" data-cy="inline-root">
    <slot />
  </component>
</template>

<style scoped>
.inline {
  display: flex;
}
</style>
