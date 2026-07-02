<script setup lang="ts">
export interface PeriodPreset {
  key: string;
  label: string;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    presets?: PeriodPreset[];
    comparison?: boolean;
  }>(),
  {
    modelValue: "",
    presets: () => [
      { key: "1m", label: "1M" },
      { key: "3m", label: "3M" },
      { key: "6m", label: "6M" },
      { key: "ytd", label: "YTD" },
      { key: "1y", label: "1Y" },
      { key: "all", label: "All" },
    ],
    comparison: false,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "update:comparison": [value: boolean];
}>();
</script>

<template>
  <div class="period-selector" data-cy="period-selector-root">
    <div class="period-selector__presets">
      <button
        v-for="preset in props.presets"
        :key="preset.key"
        type="button"
        class="period-selector__preset"
        :class="{
          'period-selector__preset--active': props.modelValue === preset.key,
        }"
        @click="emit('update:modelValue', preset.key)"
      >
        {{ preset.label }}
      </button>
    </div>

    <label v-if="comparison" class="period-selector__comparison">
      <input
        type="checkbox"
        :checked="comparison"
        @change="
          emit('update:comparison', ($event.target as HTMLInputElement).checked)
        "
      />
      <span>Compare</span>
    </label>
  </div>
</template>

<style scoped>
.period-selector {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
}

.period-selector__presets {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.period-selector__preset {
  min-height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  cursor: pointer;
}

.period-selector__preset:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.period-selector__preset--active {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-weight: 600;
}

.period-selector__comparison {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
}
</style>
