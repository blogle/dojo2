<script setup lang="ts">
import { computed, ref } from "vue";

import { useDismissableLayer } from "@/dojo/composables/useDismissableLayer";

export interface DropdownButtonItem {
  key: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    label?: string;
    items: DropdownButtonItem[];
    variant?: "primary" | "secondary";
    disabled?: boolean;
  }>(),
  {
    label: "Add",
    variant: "primary",
    disabled: false,
  },
);

const emit = defineEmits<{
  select: [key: string];
}>();

const root = ref<HTMLElement | null>(null);
const open = ref(false);
const toggleLabel = computed(() => `${props.label} options`);

const closeMenu = () => {
  open.value = false;
};

const onSelect = (item: DropdownButtonItem) => {
  if (item.disabled) {
    return;
  }

  emit("select", item.key);
  closeMenu();
};

useDismissableLayer(open, root, closeMenu);
</script>

<template>
  <div
    ref="root"
    class="dropdown-button"
    :class="`dropdown-button--${variant}`"
    data-cy="dropdown-button-root"
  >
    <button
      type="button"
      class="dropdown-button__primary"
      :disabled="disabled"
    >
      {{ label }}
    </button>

    <button
      type="button"
      class="dropdown-button__toggle"
      :aria-label="toggleLabel"
      :aria-expanded="open ? 'true' : 'false'"
      :disabled="disabled"
      @click="open = !open"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M7 10l5 5 5-5" />
      </svg>
    </button>

    <div v-if="open" class="dropdown-button__menu" role="menu">
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="dropdown-button__item"
        :disabled="item.disabled"
        role="menuitem"
        @click="onSelect(item)"
      >
        <span class="dropdown-button__item-label">{{ item.label }}</span>
        <span v-if="item.description" class="dropdown-button__item-description">{{ item.description }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.dropdown-button {
  position: relative;
  display: inline-grid;
  grid-template-columns: auto 32px;
}

.dropdown-button__primary,
.dropdown-button__toggle {
  min-height: 36px;
  border: 1px solid transparent;
  color: var(--color-on-primary);
  background: var(--color-primary);
  cursor: pointer;
}

.dropdown-button--secondary .dropdown-button__primary,
.dropdown-button--secondary .dropdown-button__toggle {
  border-color: var(--color-outline);
  color: var(--color-on-surface);
  background: var(--color-surface);
}

.dropdown-button__primary {
  padding: 0 14px;
  border-right: 0;
  border-radius: var(--radius-all) 0 0 var(--radius-all);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.dropdown-button__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  padding: 0;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0 var(--radius-all) var(--radius-all) 0;
}

.dropdown-button--secondary .dropdown-button__toggle {
  border-left-color: var(--color-outline);
}

.dropdown-button__toggle :deep(svg) {
  width: 16px;
  height: 16px;
}

.dropdown-button__primary:disabled,
.dropdown-button__toggle:disabled,
.dropdown-button__item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropdown-button__menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 200px;
  display: grid;
  padding: var(--space-xs);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-popover);
  z-index: 100;
}

.dropdown-button__item {
  display: grid;
  gap: 2px;
  padding: 8px 12px;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface);
  text-align: left;
  cursor: pointer;
}

.dropdown-button__item:hover:enabled {
  background: var(--color-surface-selected);
}

.dropdown-button__item-description {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.dropdown-button__item-label {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}
</style>
