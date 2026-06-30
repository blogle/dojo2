<script setup lang="ts">
withDefaults(
  defineProps<{
    text: string;
    position?: "top" | "bottom" | "left" | "right";
  }>(),
  {
    position: "top",
  },
);
</script>

<template>
  <span class="tooltip" data-cy="tooltip-root">
    <slot />
    <span class="tooltip__content" :class="`tooltip__content--${position}`">
      {{ text }}
    </span>
  </span>
</template>

<style scoped>
.tooltip {
  position: relative;
  display: inline-flex;
}

.tooltip__content {
  position: absolute;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-on-surface);
  color: var(--color-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-popover);
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--transition-fast) var(--transition-ease-out);
  z-index: 10;
}

.tooltip:hover .tooltip__content {
  opacity: 1;
}

.tooltip__content--top {
  bottom: calc(100% + var(--space-xs));
  left: 50%;
  transform: translateX(-50%);
}

.tooltip__content--bottom {
  top: calc(100% + var(--space-xs));
  left: 50%;
  transform: translateX(-50%);
}

.tooltip__content--left {
  right: calc(100% + var(--space-xs));
  top: 50%;
  transform: translateY(-50%);
}

.tooltip__content--right {
  left: calc(100% + var(--space-xs));
  top: 50%;
  transform: translateY(-50%);
}
</style>
