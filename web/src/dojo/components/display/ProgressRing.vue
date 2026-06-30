<script setup lang="ts">
withDefaults(
  defineProps<{
    value: number;
    size?: number;
    strokeWidth?: number;
    variant?: "positive" | "warning" | "error" | "neutral";
  }>(),
  {
    size: 80,
    strokeWidth: 6,
    variant: "neutral",
  },
);

const variantColorMap: Record<string, string> = {
  positive: "var(--color-positive)",
  warning: "var(--color-warning)",
  error: "var(--color-error)",
  neutral: "var(--color-outline-strong)",
};
</script>

<template>
  <div class="progress-ring" data-cy="progress-ring-root">
    <svg
      :width="size"
      :height="size"
      :viewBox="`0 0 ${size} ${size}`"
    >
      <circle
        class="progress-ring__track"
        :cx="size / 2"
        :cy="size / 2"
        :r="(size - strokeWidth) / 2"
        :stroke-width="strokeWidth"
      />
      <circle
        class="progress-ring__fill"
        :cx="size / 2"
        :cy="size / 2"
        :r="(size - strokeWidth) / 2"
        :stroke-width="strokeWidth"
        :stroke="variantColorMap[variant]"
        :stroke-dasharray="2 * Math.PI * ((size - strokeWidth) / 2)"
        :stroke-dashoffset="
          2 * Math.PI * ((size - strokeWidth) / 2) * (1 - Math.min(100, Math.max(0, value)) / 100)
        "
        transform-origin="center"
        transform="rotate(-90)"
      />
    </svg>
  </div>
</template>

<style scoped>
.progress-ring {
  display: inline-flex;
}

.progress-ring__track {
  fill: none;
  stroke: var(--color-surface-muted);
}

.progress-ring__fill {
  fill: none;
  stroke-linecap: round;
  transition: stroke-dashoffset var(--transition-normal) var(--transition-ease-out);
}
</style>
