<script setup lang="ts">
import StateBadge from "@/dojo/components/display/StateBadge.vue";

import type { StateBadgeVariant } from "@/dojo/components/display/StateBadge.vue";

export interface StackedEntityCardProps {
  name: string;
  primaryValue: string;
  icon?: string;
  delta?: number;
  metadata?: string;
  status?: {
    label: string;
    variant: StateBadgeVariant;
  };
  sourceOfTruth?: string;
  clickable?: boolean;
}

withDefaults(defineProps<StackedEntityCardProps>(), {
  icon: undefined,
  delta: undefined,
  metadata: undefined,
  status: undefined,
  sourceOfTruth: undefined,
  clickable: false,
});

const emit = defineEmits<{
  select: [];
}>();

const deltaClass = (delta: number | undefined) => {
  if (delta === undefined || delta === 0) {
    return "stacked-entity-card__delta--neutral";
  }
  return delta > 0
    ? "stacked-entity-card__delta--positive"
    : "stacked-entity-card__delta--negative";
};

const formatDelta = (delta: number) => `${delta > 0 ? "+" : ""}${delta}`;
</script>

<template>
  <div
    :class="[
      'stacked-entity-card',
      { 'stacked-entity-card--clickable': clickable },
    ]"
    :role="clickable ? 'button' : undefined"
    :tabindex="clickable ? 0 : undefined"
    data-cy="stacked-entity-card-root"
    @click="clickable && emit('select')"
    @keydown.enter="clickable && emit('select')"
    @keydown.space.prevent="clickable && emit('select')"
  >
    <div class="stacked-entity-card__icon" v-if="icon">
      <svg
        class="stacked-entity-card__icon-svg"
        viewBox="0 0 18 18"
        fill="none"
        aria-hidden="true"
      >
        <circle cx="9" cy="9" r="7" fill="currentColor" opacity="0.15" />
        <path
          d="M9 6v6M6 9h6"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
    </div>
    <div class="stacked-entity-card__content">
      <div class="stacked-entity-card__header">
        <span class="stacked-entity-card__name">{{ name }}</span>
        <StateBadge v-if="status" :variant="status.variant" size="sm">
          {{ status.label }}
        </StateBadge>
      </div>
      <div class="stacked-entity-card__body">
        <span class="stacked-entity-card__value">{{ primaryValue }}</span>
        <span
          v-if="delta !== undefined"
          :class="['stacked-entity-card__delta', deltaClass(delta)]"
        >
          {{ formatDelta(delta) }}
        </span>
      </div>
      <div class="stacked-entity-card__footer" v-if="metadata || sourceOfTruth">
        <span v-if="metadata" class="stacked-entity-card__metadata">{{
          metadata
        }}</span>
        <span v-if="sourceOfTruth" class="stacked-entity-card__source-of-truth">
          {{ sourceOfTruth }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stacked-entity-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  transition: background var(--transition-fast) var(--ease-out);
}

.stacked-entity-card--clickable {
  cursor: pointer;
}

.stacked-entity-card--clickable:hover {
  background: var(--color-surface-selected);
}

.stacked-entity-card__icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  color: var(--color-secondary);
}

.stacked-entity-card__icon-svg {
  width: 100%;
  height: 100%;
}

.stacked-entity-card__content {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 6px;
}

.stacked-entity-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.stacked-entity-card__name {
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.stacked-entity-card__body {
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
}

.stacked-entity-card__value {
  color: var(--color-on-surface);
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.stacked-entity-card__delta {
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.stacked-entity-card__delta--positive {
  color: var(--color-positive);
}

.stacked-entity-card__delta--negative {
  color: var(--color-error);
}

.stacked-entity-card__delta--neutral {
  color: var(--color-on-surface-muted);
}

.stacked-entity-card__footer {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.stacked-entity-card__metadata {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.stacked-entity-card__source-of-truth {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 2px 8px;
  background: var(--color-info-container);
  color: var(--color-info);
  border-radius: var(--radius-all);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}
</style>
