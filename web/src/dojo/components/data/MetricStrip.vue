<script setup lang="ts">
import StateBadge from "@/dojo/components/display/StateBadge.vue";

import type { StateBadgeVariant } from "@/dojo/components/display/StateBadge.vue";

export interface MetricStripItem {
  key: string;
  label: string;
  value?: string;
  auxValue?: string;
  delta?: number;
  loading?: boolean;
  status?: {
    label: string;
    variant: StateBadgeVariant;
  };
  clickable?: boolean;
}

const props = withDefaults(
  defineProps<{
    items: MetricStripItem[];
    scrollable?: boolean;
  }>(),
  {
    scrollable: false,
  },
);

const emit = defineEmits<{
  select: [key: string];
}>();

const deltaClass = (delta: number | undefined) => {
  if (delta === undefined || delta === 0) {
    return "metric-strip__delta--neutral";
  }

  return delta > 0
    ? "metric-strip__delta--positive"
    : "metric-strip__delta--negative";
};

const formatDelta = (delta: number) => `${delta > 0 ? "+" : ""}${delta}`;
</script>

<template>
  <div
    class="metric-strip"
    :class="{ 'metric-strip--scrollable': scrollable }"
    data-cy="metric-strip-root"
  >
    <div
      v-for="item in props.items"
      :key="item.key"
      class="metric-strip__item"
      :class="{ 'metric-strip__item--clickable': item.clickable }"
      :role="item.clickable ? 'button' : undefined"
      :tabindex="item.clickable ? 0 : undefined"
      @click="item.clickable && emit('select', item.key)"
      @keydown.enter="item.clickable && emit('select', item.key)"
      @keydown.space.prevent="item.clickable && emit('select', item.key)"
    >
      <slot name="item" :item="item">
        <p class="metric-strip__label">{{ item.label }}</p>
        <div v-if="item.loading" class="metric-strip__skeleton" />
        <p v-else class="metric-strip__value">{{ item.value }}</p>
        <div class="metric-strip__aux-row">
          <span v-if="item.auxValue" class="metric-strip__aux-value">{{ item.auxValue }}</span>
          <span v-if="item.delta !== undefined" :class="['metric-strip__delta', deltaClass(item.delta)]">
            {{ formatDelta(item.delta) }}
          </span>
          <StateBadge
            v-if="item.status"
            :variant="item.status.variant"
            size="sm"
          >
            {{ item.status.label }}
          </StateBadge>
        </div>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.metric-strip {
  display: flex;
  gap: 0;
  padding: var(--space-lg) 0;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
}

.metric-strip--scrollable {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.metric-strip__item {
  min-width: 140px;
  display: grid;
  gap: 2px;
  padding: 0 var(--space-lg);
  border-right: 1px solid var(--color-outline);
}

.metric-strip__item:last-child {
  border-right: 0;
}

.metric-strip__item--clickable {
  cursor: pointer;
}

.metric-strip__label,
.metric-strip__value,
.metric-strip__aux-value,
.metric-strip__delta {
  margin: 0;
}

.metric-strip__label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.metric-strip__value {
  color: var(--color-on-surface);
  font-family: var(--text-metric-lg-font-family);
  font-size: var(--text-metric-lg-font-size);
  font-weight: var(--text-metric-lg-font-weight);
  line-height: var(--text-metric-lg-line-height);
  letter-spacing: var(--text-metric-lg-letter-spacing);
  font-feature-settings: var(--text-metric-lg-font-feature, "tnum" 1, "zero" 1);
}

.metric-strip__aux-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.metric-strip__aux-value,
.metric-strip__delta {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.metric-strip__delta--positive {
  color: var(--color-positive);
  font-weight: 600;
}

.metric-strip__delta--negative {
  color: var(--color-error);
  font-weight: 600;
}

.metric-strip__skeleton {
  width: 80%;
  height: 28px;
  border-radius: var(--radius-all);
  background: var(--color-surface-muted);
  animation: metric-strip-pulse 1.5s ease-in-out infinite;
}

@keyframes metric-strip-pulse {
  0%,
  100% {
    opacity: 0.7;
  }

  50% {
    opacity: 1;
  }
}
</style>
