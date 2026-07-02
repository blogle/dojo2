<script setup lang="ts">
import { computed, ref } from "vue";

import Button from "../actions/Button.vue";
import IconGlyph from "../display/IconGlyph.vue";

const iconOptions = [
  { value: "groceries", label: "Groceries" },
  { value: "home", label: "Home" },
  { value: "car", label: "Car" },
  { value: "utilities", label: "Utilities" },
  { value: "dining", label: "Dining" },
  { value: "medical", label: "Medical" },
  { value: "travel", label: "Travel" },
  { value: "savings", label: "Savings" },
  { value: "debt", label: "Debt" },
  { value: "gift", label: "Gift" },
  { value: "pet", label: "Pet" },
  { value: "education", label: "Education" },
  { value: "entertainment", label: "Entertainment" },
];

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    label?: string;
    helper?: string;
  }>(),
  {
    modelValue: null,
    label: "Icon",
    helper: undefined,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
}>();

const open = ref(false);
const selectedOption = computed(() =>
  iconOptions.find((option) => option.value === props.modelValue),
);

function selectIcon(value: string | null) {
  emit("update:modelValue", value);
  open.value = false;
}
</script>

<template>
  <div class="icon-picker" data-cy="icon-picker-root">
    <span v-if="label" class="icon-picker__label">{{ label }}</span>
    <button
      type="button"
      class="icon-picker__trigger"
      data-cy="icon-picker-trigger"
      @click="open = !open"
    >
      <span class="icon-picker__preview">
        <IconGlyph :name="modelValue" />
      </span>
      <span class="icon-picker__trigger-copy">
        <span class="icon-picker__trigger-label">{{
          selectedOption?.label ?? "Choose icon"
        }}</span>
        <span class="icon-picker__trigger-helper"
          >Pick from the dojo icon pack</span
        >
      </span>
      <span class="icon-picker__chevron" aria-hidden="true">▾</span>
    </button>
    <span v-if="helper" class="icon-picker__message">{{ helper }}</span>

    <div
      v-if="open"
      class="icon-picker__dialog"
      role="dialog"
      aria-label="Choose category icon"
    >
      <div class="icon-picker__grid">
        <button
          v-for="option in iconOptions"
          :key="option.value"
          type="button"
          class="icon-picker__option"
          :class="{
            'icon-picker__option--selected': modelValue === option.value,
          }"
          @click="selectIcon(option.value)"
        >
          <IconGlyph :name="option.value" />
          <span>{{ option.label }}</span>
        </button>
      </div>
      <div class="icon-picker__footer">
        <Button variant="tertiary" size="sm" @click="selectIcon(null)"
          >Clear</Button
        >
        <Button variant="secondary" size="sm" @click="open = false"
          >Close</Button
        >
      </div>
    </div>
  </div>
</template>

<style scoped>
.icon-picker {
  position: relative;
  display: grid;
  gap: var(--space-xs);
}

.icon-picker__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.icon-picker__trigger {
  width: 100%;
  min-height: 48px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--space-sm);
  align-items: center;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  padding: var(--space-xs) var(--space-sm);
  text-align: left;
  cursor: pointer;
}

.icon-picker__preview,
.icon-picker__option :deep(.icon-glyph) {
  width: 28px;
  height: 28px;
}

.icon-picker__preview {
  display: grid;
  place-items: center;
  border-radius: var(--radius-all);
  background: var(--color-surface-muted);
  color: var(--color-primary);
  font-size: 18px;
}

.icon-picker__trigger-copy {
  display: grid;
  gap: 1px;
}

.icon-picker__trigger-label {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: 600;
}

.icon-picker__trigger-helper,
.icon-picker__message {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.icon-picker__chevron {
  color: var(--color-on-surface-muted);
}

.icon-picker__dialog {
  position: absolute;
  z-index: 260;
  top: calc(100% + var(--space-xs));
  left: 0;
  right: 0;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-modal);
  padding: var(--space-md);
  display: grid;
  gap: var(--space-md);
}

.icon-picker__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
}

.icon-picker__option {
  min-height: 72px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: var(--space-xs);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  cursor: pointer;
}

.icon-picker__option:hover,
.icon-picker__option--selected {
  border-color: var(--color-primary);
  background: var(--color-surface-selected);
  color: var(--color-primary);
}

.icon-picker__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}

@media (max-width: 560px) {
  .icon-picker__grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
