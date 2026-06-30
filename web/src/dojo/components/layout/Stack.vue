<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    gap?: string;
    tag?: string;
  }>(),
  {
    gap: "var(--space-lg)",
    tag: "div",
  },
);

const style = computed(() => ({
  gap: props.gap,
}));
</script>

<template>
  <component :is="tag" class="stack" :style="style" data-cy="stack-root">
    <slot />
  </component>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
}
</style>
