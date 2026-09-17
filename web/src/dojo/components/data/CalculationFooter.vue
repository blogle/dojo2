<script setup lang="ts">
defineProps<{
  label: string;
  value: string;
}>();
</script>

<template>
  <footer class="calculation-footer" data-cy="calculation-footer">
    <span class="calculation-footer__label" data-cy="calculation-footer-label">
      {{ label }}
    </span>
    <strong
      class="calculation-footer__value"
      data-cy="calculation-footer-value"
    >
      {{ value }}
    </strong>
  </footer>
</template>

<style scoped>
.calculation-footer {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-outline-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-popover);
}

.calculation-footer__label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.calculation-footer__value {
  min-width: 8ch;
  color: var(--color-on-surface);
  font-family: var(--text-metric-md-font-family);
  font-size: var(--text-metric-md-font-size);
  font-weight: var(--text-metric-md-font-weight);
  line-height: var(--text-metric-md-line-height);
  text-align: right;
  font-feature-settings: var(--text-metric-md-font-feature, "tnum" 1, "zero" 1);
}

@media (max-width: 480px) {
  .calculation-footer {
    gap: var(--space-sm);
    padding-inline: var(--space-md);
  }
}
</style>
