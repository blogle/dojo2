<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    orientation?: "horizontal" | "vertical";
    size?: string;
    color?: string;
  }>(),
  {
    orientation: "horizontal",
    size: "1px",
    color: "var(--color-outline)",
  },
);

const style = computed(() =>
  props.orientation === "horizontal"
    ? { borderTop: `${props.size} solid ${props.color}` }
    : { borderLeft: `${props.size} solid ${props.color}`, height: "100%" },
);
</script>

<template>
  <hr :class="['divider', `divider--${orientation}`]" :style="style" data-cy="divider-root" />
</template>

<style scoped>
.divider {
  margin: 0;
  border: 0;
}

.divider--horizontal {
  width: 100%;
}

.divider--vertical {
  align-self: stretch;
}
</style>
