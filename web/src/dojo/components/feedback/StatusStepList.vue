<script setup lang="ts">
import { PhCheck, PhCircle, PhCircleNotch } from "@phosphor-icons/vue";

export interface StatusStep {
  title: string;
  description: string;
  status: "complete" | "in-progress" | "pending";
}

defineProps<{
  steps: StatusStep[];
}>();
</script>

<template>
  <ul class="status-step-list" data-cy="status-step-list-root">
    <li
      v-for="(step, index) in steps"
      :key="index"
      class="status-step-list__item"
    >
      <span
        :class="[
          'status-step-list__icon',
          `status-step-list__icon--${step.status}`,
        ]"
        aria-hidden="true"
      >
        <PhCheck
          v-if="step.status === 'complete'"
          class="status-step-list__svg"
          :size="20"
          weight="bold"
        />
        <PhCircleNotch
          v-else-if="step.status === 'in-progress'"
          class="status-step-list__spinner"
          :size="20"
        />
        <PhCircle v-else class="status-step-list__svg" :size="20" />
      </span>
      <div class="status-step-list__copy">
        <span class="status-step-list__title">{{ step.title }}</span>
        <span class="status-step-list__description">{{
          step.description
        }}</span>
      </div>
      <span
        :class="[
          'status-step-list__badge',
          `status-step-list__badge--${step.status}`,
        ]"
      >
        {{
          step.status === "complete"
            ? "Complete"
            : step.status === "in-progress"
              ? "In progress"
              : "Pending"
        }}
      </span>
    </li>
  </ul>
</template>

<style scoped>
.status-step-list {
  display: grid;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}

.status-step-list__item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) 0;
}

.status-step-list__item + .status-step-list__item {
  border-top: 1px solid var(--color-outline);
}

.status-step-list__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
}

.status-step-list__icon--complete {
  background: var(--color-positive-container);
  color: var(--color-positive);
}

.status-step-list__icon--in-progress {
  background: var(--color-warning-container);
  color: var(--color-warning);
}

.status-step-list__icon--pending {
  background: var(--color-surface-muted);
  color: var(--color-outline-strong);
}

.status-step-list__svg {
  width: 20px;
  height: 20px;
}

.status-step-list__spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.status-step-list__copy {
  display: grid;
  gap: var(--space-xs);
}

.status-step-list__title {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-body-md-line-height);
  color: var(--color-on-surface);
}

.status-step-list__description {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}

.status-step-list__badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-all);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  white-space: nowrap;
}

.status-step-list__badge--complete {
  background: var(--color-positive-container);
  color: var(--color-positive);
}

.status-step-list__badge--in-progress {
  background: var(--color-warning-container);
  color: var(--color-warning);
}

.status-step-list__badge--pending {
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
}
</style>
