<script setup lang="ts">
export interface KeyValueItem {
  label: string;
  value: string;
  variant?: "positive" | "warning" | "error";
}

defineProps<{
  items: KeyValueItem[];
}>();
</script>

<template>
  <dl class="key-value-list" data-cy="key-value-list-root">
    <div
      v-for="(item, index) in items"
      :key="index"
      class="key-value-list__row"
    >
      <dt class="key-value-list__label">{{ item.label }}</dt>
      <dd
        :class="[
          'key-value-list__value',
          item.variant ? `key-value-list__value--${item.variant}` : '',
        ]"
      >
        {{ item.value }}
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.key-value-list {
  display: grid;
  gap: var(--space-sm);
}

.key-value-list__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.key-value-list__label {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}

.key-value-list__value {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  color: var(--color-on-surface);
}

.key-value-list__value--positive {
  color: var(--color-positive);
}

.key-value-list__value--warning {
  color: var(--color-warning);
}

.key-value-list__value--error {
  color: var(--color-error);
}
</style>
