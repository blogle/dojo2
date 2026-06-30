<script setup lang="ts">
export interface TabItem {
  key: string;
  label: string;
}

withDefaults(
  defineProps<{
    modelValue?: string;
    items: TabItem[];
  }>(),
  {
    modelValue: "",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <div class="tabs" role="tablist" data-cy="tabs-root">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      class="tabs__item"
      :class="{ 'tabs__item--active': modelValue === item.key }"
      role="tab"
      :aria-selected="modelValue === item.key ? 'true' : 'false'"
      @click="emit('update:modelValue', item.key)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<style scoped>
.tabs {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.tabs__item {
  min-height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-primary);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  cursor: pointer;
}

.tabs__item:hover {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.tabs__item--active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-weight: 600;
}
</style>
