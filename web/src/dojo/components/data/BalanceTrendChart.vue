<script setup lang="ts">
import { computed, ref } from "vue";

import PeriodSelector from "./PeriodSelector.vue";
import { formatCurrency } from "@/dojo/utils/currency";

export type BalanceTrendPoint = {
  date: string;
  valueMinor: number;
};

const props = withDefaults(
  defineProps<{
    points: BalanceTrendPoint[];
    period: string;
  }>(),
  { points: () => [] },
);

const emit = defineEmits<{
  "update:period": [value: string];
}>();

const width = 720;
const height = 260;
const pad = { top: 18, right: 24, bottom: 34, left: 72 };
const plotWidth = width - pad.left - pad.right;
const plotHeight = height - pad.top - pad.bottom;

const hoverIndex = ref<number | null>(null);
const dragStartIndex = ref<number | null>(null);
const dragEndIndex = ref<number | null>(null);
const isDragging = ref(false);

const presets = [
  { key: "7d", label: "7D" },
  { key: "1m", label: "1M" },
  { key: "3m", label: "3M" },
  { key: "6m", label: "6M" },
  { key: "1y", label: "1Y" },
  { key: "all", label: "All" },
];

const visiblePoints = computed(() => {
  const sorted = [...props.points].sort((a, b) => a.date.localeCompare(b.date));
  if (props.period === "all" || sorted.length === 0) return sorted;
  const last = new Date(`${sorted[sorted.length - 1].date}T00:00:00`);
  const days = { "7d": 7, "1m": 31, "3m": 93, "6m": 186, "1y": 366 }[
    props.period
  ];
  if (!days) return sorted;
  const start = new Date(last);
  start.setDate(last.getDate() - days);
  const startKey = start.toISOString().slice(0, 10);
  return sorted.filter((point) => point.date >= startKey);
});

const valueExtent = computed(() => {
  const values = visiblePoints.value.map((point) => point.valueMinor);
  if (values.length === 0) return { min: 0, max: 1 };
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return { min: min - 100, max: max + 100 };
  const padding = Math.round((max - min) * 0.12);
  return { min: min - padding, max: max + padding };
});

const plottedPoints = computed(() =>
  visiblePoints.value.map((point, index, all) => {
    const x =
      pad.left +
      (all.length === 1 ? 0 : (index / (all.length - 1)) * plotWidth);
    const valueRange = valueExtent.value.max - valueExtent.value.min;
    const y =
      pad.top +
      plotHeight -
      ((point.valueMinor - valueExtent.value.min) / valueRange) * plotHeight;
    return { ...point, x, y };
  }),
);

const linePath = computed(() => {
  if (plottedPoints.value.length === 0) return "";
  return plottedPoints.value
    .map((point, index) => `${index === 0 ? "M" : "L"}${point.x} ${point.y}`)
    .join(" ");
});

const areaPath = computed(() => {
  if (plottedPoints.value.length === 0) return "";
  const first = plottedPoints.value[0];
  const last = plottedPoints.value[plottedPoints.value.length - 1];
  return `${linePath.value} L${last.x} ${pad.top + plotHeight} L${first.x} ${
    pad.top + plotHeight
  } Z`;
});

const yTicks = computed(() => {
  const { min, max } = valueExtent.value;
  return [0, 0.5, 1].map((ratio) => {
    const value = Math.round(min + (max - min) * (1 - ratio));
    return { value, y: pad.top + plotHeight * ratio };
  });
});

const xTicks = computed(() => {
  const points = plottedPoints.value;
  if (points.length === 0) return [];
  const candidates = [
    points[0],
    points[Math.floor(points.length / 2)],
    points[points.length - 1],
  ];
  return candidates.filter(Boolean);
});

const activeIndex = computed(() => dragEndIndex.value ?? hoverIndex.value);
const activePoint = computed(() =>
  activeIndex.value === null ? null : plottedPoints.value[activeIndex.value],
);
const measurement = computed(() => {
  const startIndex = dragStartIndex.value;
  const endIndex = dragEndIndex.value;
  if (startIndex === null || endIndex === null) return null;
  const start = plottedPoints.value[Math.min(startIndex, endIndex)];
  const end = plottedPoints.value[Math.max(startIndex, endIndex)];
  if (!start || !end) return null;
  return { start, end, delta: end.valueMinor - start.valueMinor };
});

const tooltipText = computed(() => {
  if (measurement.value) {
    return `${formatDate(measurement.value.start.date)} to ${formatDate(
      measurement.value.end.date,
    )}: ${formatCurrency(measurement.value.delta)} growth (${formatCurrency(
      measurement.value.start.valueMinor,
    )} -> ${formatCurrency(measurement.value.end.valueMinor)})`;
  }
  if (!activePoint.value || plottedPoints.value.length === 0) return "";
  const first = plottedPoints.value[0];
  const delta = activePoint.value.valueMinor - first.valueMinor;
  return `${formatDate(activePoint.value.date)}: ${formatCurrency(
    activePoint.value.valueMinor,
  )} (${formatCurrency(delta)} growth)`;
});

const tooltipPosition = computed(() => {
  const point = activePoint.value;
  if (!point) return { x: 0, y: 0 };
  return {
    x: Math.min(point.x + 10, width - 260),
    y: Math.max(point.y - 44, 8),
  };
});

function nearestIndex(event: PointerEvent): number | null {
  const target = event.currentTarget as SVGSVGElement;
  const rect = target.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * width;
  if (plottedPoints.value.length === 0) return null;
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  plottedPoints.value.forEach((point, index) => {
    const distance = Math.abs(point.x - x);
    if (distance < bestDistance) {
      bestIndex = index;
      bestDistance = distance;
    }
  });
  return bestIndex;
}

function handlePointerMove(event: PointerEvent) {
  const index = nearestIndex(event);
  if (index === null) return;
  hoverIndex.value = index;
  if (isDragging.value) {
    dragEndIndex.value = index;
  }
}

function handlePointerDown(event: PointerEvent) {
  const index = nearestIndex(event);
  if (index === null) return;
  isDragging.value = true;
  dragStartIndex.value = index;
  dragEndIndex.value = index;
  (event.currentTarget as SVGSVGElement).setPointerCapture(event.pointerId);
}

function handlePointerUp(event: PointerEvent) {
  isDragging.value = false;
  (event.currentTarget as SVGSVGElement).releasePointerCapture(event.pointerId);
}

function handlePointerLeave() {
  if (isDragging.value) return;
  hoverIndex.value = null;
  dragStartIndex.value = null;
  dragEndIndex.value = null;
}

function formatDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}
</script>

<template>
  <section class="balance-chart" data-cy="balance-trend-chart">
    <header class="balance-chart__header">
      <div>
        <h2 class="balance-chart__title">Balance over time</h2>
        <p v-if="visiblePoints.length" class="balance-chart__subtitle">
          {{
            formatCurrency(visiblePoints[visiblePoints.length - 1].valueMinor)
          }}
          as of
          {{ formatDate(visiblePoints[visiblePoints.length - 1].date) }}
        </p>
      </div>
      <PeriodSelector
        :model-value="period"
        :presets="presets"
        @update:model-value="emit('update:period', $event)"
      />
    </header>

    <svg
      class="balance-chart__svg"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      aria-label="Balance over time"
      @pointermove="handlePointerMove"
      @pointerdown="handlePointerDown"
      @pointerup="handlePointerUp"
      @pointerleave="handlePointerLeave"
    >
      <g class="balance-chart__grid">
        <line
          v-for="tick in yTicks"
          :key="tick.y"
          :x1="pad.left"
          :x2="width - pad.right"
          :y1="tick.y"
          :y2="tick.y"
        />
      </g>
      <g class="balance-chart__axis-labels">
        <text v-for="tick in yTicks" :key="tick.value" x="8" :y="tick.y + 4">
          {{ formatCurrency(tick.value) }}
        </text>
        <text
          v-for="tick in xTicks"
          :key="tick.date"
          :x="tick.x"
          :y="height - 8"
          text-anchor="middle"
        >
          {{ formatDate(tick.date) }}
        </text>
      </g>
      <path v-if="areaPath" class="balance-chart__area" :d="areaPath" />
      <path v-if="linePath" class="balance-chart__line" :d="linePath" />
      <template v-if="activePoint">
        <line
          class="balance-chart__crosshair"
          :x1="activePoint.x"
          :x2="activePoint.x"
          :y1="pad.top"
          :y2="pad.top + plotHeight"
        />
        <circle
          class="balance-chart__dot"
          :cx="activePoint.x"
          :cy="activePoint.y"
          r="4"
        />
      </template>
      <template v-if="measurement">
        <rect
          class="balance-chart__measure-band"
          :x="Math.min(measurement.start.x, measurement.end.x)"
          :width="Math.abs(measurement.end.x - measurement.start.x)"
          :y="pad.top"
          :height="plotHeight"
        />
      </template>
      <foreignObject
        v-if="tooltipText"
        class="balance-chart__tooltip-host"
        :x="tooltipPosition.x"
        :y="tooltipPosition.y"
        width="250"
        height="64"
      >
        <div class="balance-chart__tooltip">{{ tooltipText }}</div>
      </foreignObject>
    </svg>
  </section>
</template>

<style scoped>
.balance-chart {
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  overflow: hidden;
}

.balance-chart__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
}

.balance-chart__title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
}

.balance-chart__subtitle {
  margin: var(--space-xs) 0 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.balance-chart__svg {
  display: block;
  width: 100%;
  height: auto;
  touch-action: none;
  user-select: none;
}

.balance-chart__grid line {
  stroke: var(--color-outline);
  stroke-width: 1;
}

.balance-chart__axis-labels text {
  fill: var(--color-on-surface-muted);
  font-family: var(--text-caption-font-family);
  font-size: var(--text-caption-font-size);
}

.balance-chart__area {
  fill: var(--color-positive-container);
  opacity: 0.55;
}

.balance-chart__line {
  fill: none;
  stroke: var(--color-positive);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.balance-chart__crosshair {
  stroke: var(--color-outline-strong);
  stroke-width: 1;
  stroke-dasharray: 3 3;
}

.balance-chart__dot {
  fill: var(--color-surface-raised);
  stroke: var(--color-positive);
  stroke-width: 2;
}

.balance-chart__measure-band {
  fill: var(--color-primary-container);
  opacity: 0.35;
}

.balance-chart__tooltip-host {
  overflow: visible;
}

.balance-chart__tooltip {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-outline-strong);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-popover);
  color: var(--color-on-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

@media (max-width: 720px) {
  .balance-chart__header {
    display: grid;
  }
}
</style>
