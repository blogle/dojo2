<script setup lang="ts">
import {
  TooltipContent,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
} from "reka-ui";

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
  <TooltipProvider :delay-duration="0">
    <TooltipRoot>
      <TooltipTrigger class="tooltip" data-cy="tooltip-root">
        <slot />
      </TooltipTrigger>
      <TooltipContent
        class="tooltip__content"
        :class="`tooltip__content--${position}`"
        :side="position"
        :side-offset="8"
      >
        {{ text }}
      </TooltipContent>
    </TooltipRoot>
  </TooltipProvider>
</template>

<style scoped>
.tooltip {
  position: relative;
  display: inline-flex;
  border: 0;
  padding: 0;
  background: transparent;
}

.tooltip__content {
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
  z-index: 10;
}
</style>
