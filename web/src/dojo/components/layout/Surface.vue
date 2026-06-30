<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    variant?: "paper" | "muted" | "raised" | "transparent";
    padding?: string;
    radius?: string;
    border?: boolean;
    tag?: string;
  }>(),
  {
    variant: "paper",
    padding: "var(--space-md)",
    radius: "var(--radius-all)",
    border: true,
    tag: "div",
  },
);

const style = computed(() => ({
  padding: props.padding,
  borderRadius: props.radius,
}));
</script>

<template>
  <component
    :is="tag"
    :class="['surface', `surface--${variant}`, { 'surface--border': border }]"
    :style="style"
    data-cy="surface-root"
  >
    <slot />
  </component>
</template>

<style scoped>
.surface {
  color: var(--color-on-surface);
}

.surface--border {
  border: 1px solid var(--color-outline);
}

.surface--paper {
  background: var(--color-surface);
}

.surface--muted {
  background: var(--color-surface-muted);
}

.surface--raised {
  background: var(--color-surface-raised);
}

.surface--transparent {
  background: transparent;
}
</style>
