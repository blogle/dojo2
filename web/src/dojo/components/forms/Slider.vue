<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue?: number;
    min?: number;
    max?: number;
    step?: number;
    label?: string;
    disabled?: boolean;
    minLabel?: string;
    maxLabel?: string;
  }>(),
  {
    modelValue: 0,
    min: 0,
    max: 100,
    step: 1,
    label: undefined,
    disabled: false,
    minLabel: undefined,
    maxLabel: undefined,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();
</script>

<template>
  <div class="slider" data-cy="slider-root">
    <span v-if="label" class="slider__label">{{ label }}</span>

    <div class="slider__track-wrapper">
      <input
        class="slider__input"
        type="range"
        :value="modelValue"
        :min="min"
        :max="max"
        :step="step"
        :disabled="disabled"
        @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
      />
    </div>

    <div class="slider__range-labels">
      <span v-if="minLabel" class="slider__range-label">{{ minLabel }}</span>
      <span v-if="maxLabel" class="slider__range-label">{{ maxLabel }}</span>
    </div>
  </div>
</template>

<style scoped>
.slider {
  display: grid;
  gap: var(--space-xs);
}

.slider__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.slider__track-wrapper {
  display: flex;
  align-items: center;
}

.slider__input {
  width: 100%;
  height: 6px;
  appearance: none;
  background: var(--color-surface-muted);
  border-radius: var(--radius-full);
  outline: none;
}

.slider__input::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-on-primary);
  box-shadow: var(--shadow-popover);
}

.slider__input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-on-primary);
  box-shadow: var(--shadow-popover);
}

.slider__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.slider__input:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
}

.slider__input:disabled::-moz-range-thumb {
  cursor: not-allowed;
}

.slider__range-labels {
  display: flex;
  justify-content: space-between;
}

.slider__range-label {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}
</style>
