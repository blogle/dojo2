<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  useId,
  watch,
} from "vue";

export interface ComboboxOption {
  value: string;
  label: string;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    options: ComboboxOption[];
    label?: string;
    placeholder?: string;
    disabled?: boolean;
    allowCustom?: boolean;
    invalid?: boolean;
  }>(),
  {
    modelValue: "",
    label: undefined,
    placeholder: "Select an option...",
    disabled: false,
    allowCustom: false,
    invalid: false,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  focus: [];
  blur: [];
}>();

const root = ref<HTMLElement | null>(null);
const trigger = ref<HTMLButtonElement | null>(null);
const searchInput = ref<HTMLInputElement | null>(null);
const query = ref("");
const isOpen = ref(false);
const activeIndex = ref(-1);
const id = useId();
const listId = `combobox-options-${id}`;
const triggerId = `combobox-trigger-${id}`;
const searchId = `combobox-search-${id}`;

const selectedOption = computed(() =>
  props.options.find((option) => option.value === props.modelValue),
);
const displayValue = computed(
  () =>
    selectedOption.value?.label ??
    (props.allowCustom && props.modelValue
      ? props.modelValue
      : props.placeholder),
);
const isInvalid = computed(
  () =>
    props.invalid ||
    Boolean(props.modelValue && !selectedOption.value && !props.allowCustom),
);
const filteredOptions = computed(() => {
  const normalizedQuery = query.value.trim().toLocaleLowerCase();
  return props.options.filter((option) =>
    option.label.toLocaleLowerCase().includes(normalizedQuery),
  );
});
const activeOptionId = computed(() =>
  activeIndex.value >= 0 ? `${listId}-option-${activeIndex.value}` : undefined,
);

watch(
  () => props.options,
  () => {
    if (activeIndex.value >= filteredOptions.value.length)
      activeIndex.value = -1;
  },
);

async function openPopover() {
  if (props.disabled) return;
  query.value = props.allowCustom ? props.modelValue : "";
  activeIndex.value = -1;
  isOpen.value = true;
  emit("focus");
  await nextTick();
  searchInput.value?.focus();
}

function closePopover({ restoreFocus = false } = {}) {
  isOpen.value = false;
  activeIndex.value = -1;
  query.value = props.allowCustom ? props.modelValue : "";
  if (restoreFocus) void nextTick(() => trigger.value?.focus());
  emit("blur");
}

function selectOption(option: ComboboxOption) {
  if (option.disabled) return;
  emit("update:modelValue", option.value);
  closePopover({ restoreFocus: true });
}

function moveActiveOption(direction: -1 | 1) {
  if (!filteredOptions.value.length) return;
  let nextIndex = activeIndex.value;
  for (let count = 0; count < filteredOptions.value.length; count += 1) {
    nextIndex =
      (nextIndex + direction + filteredOptions.value.length) %
      filteredOptions.value.length;
    if (!filteredOptions.value[nextIndex]?.disabled) {
      activeIndex.value = nextIndex;
      return;
    }
  }
}

function handleTriggerKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" || event.key === " " || event.key === "ArrowDown") {
    event.preventDefault();
    void openPopover().then(() => {
      if (event.key === "ArrowDown") moveActiveOption(1);
    });
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    void openPopover().then(() => moveActiveOption(-1));
  }
}

function handleSearchInput(event: Event) {
  query.value = (event.target as HTMLInputElement).value;
  activeIndex.value = -1;
  if (props.allowCustom) emit("update:modelValue", query.value);
}

function handleSearchKeydown(event: KeyboardEvent) {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    moveActiveOption(event.key === "ArrowDown" ? 1 : -1);
  } else if (event.key === "Enter" && isOpen.value) {
    event.preventDefault();
    const option = filteredOptions.value[activeIndex.value];
    if (option) {
      selectOption(option);
    }
  } else if (event.key === "Escape") {
    event.preventDefault();
    closePopover({ restoreFocus: true });
  } else if (event.key === "Tab") {
    closePopover();
  }
}

function handleOutsidePointer(event: PointerEvent) {
  if (isOpen.value && !root.value?.contains(event.target as Node)) {
    closePopover();
  }
}

onMounted(() => document.addEventListener("pointerdown", handleOutsidePointer));
onUnmounted(() =>
  document.removeEventListener("pointerdown", handleOutsidePointer),
);
</script>

<template>
  <div ref="root" class="combobox-field" data-cy="combobox-field-root">
    <label class="combobox-field__label" :for="triggerId">{{ label }}</label>
    <button
      :id="triggerId"
      ref="trigger"
      class="combobox-field__trigger"
      data-cy="combobox-field-trigger"
      type="button"
      role="combobox"
      aria-haspopup="listbox"
      :aria-expanded="isOpen"
      :aria-controls="listId"
      :aria-activedescendant="activeOptionId"
      :aria-invalid="isInvalid"
      :disabled="disabled"
      @click="isOpen ? closePopover() : openPopover()"
      @keydown="handleTriggerKeydown"
    >
      <span
        class="combobox-field__value"
        :class="{ 'combobox-field__value--placeholder': !modelValue }"
      >
        {{ displayValue }}
      </span>
      <span class="combobox-field__chevron" aria-hidden="true">▾</span>
    </button>
    <div v-if="isOpen" class="combobox-field__popover">
      <input
        :id="searchId"
        ref="searchInput"
        class="combobox-field__search"
        data-cy="combobox-field-search"
        type="search"
        role="searchbox"
        :aria-label="`Search ${label}`"
        :aria-controls="listId"
        :aria-activedescendant="activeOptionId"
        :value="query"
        placeholder="Type to filter..."
        autocomplete="off"
        @input="handleSearchInput"
        @keydown="handleSearchKeydown"
      />
      <ul
        :id="listId"
        class="combobox-field__options"
        role="listbox"
        :aria-label="label"
      >
        <li
          v-for="(option, index) in filteredOptions"
          :id="`${listId}-option-${index}`"
          :key="option.value"
          class="combobox-field__option"
          :class="{
            'combobox-field__option--active': activeIndex === index,
            'combobox-field__option--disabled': option.disabled,
          }"
          role="option"
          :aria-selected="option.value === modelValue"
          :aria-disabled="option.disabled || undefined"
          @pointerdown.prevent
          @click="selectOption(option)"
        >
          {{ option.label }}
        </li>
        <li
          v-if="filteredOptions.length === 0"
          class="combobox-field__empty"
          role="status"
        >
          No matching options
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.combobox-field {
  position: relative;
  display: grid;
  gap: var(--space-xs);
  min-width: 0;
}

.combobox-field__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.combobox-field__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  width: 100%;
  min-height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  text-align: left;
  cursor: pointer;
}

.combobox-field__trigger:focus-visible,
.combobox-field__search:focus-visible,
.combobox-field__option:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.combobox-field__trigger[aria-invalid="true"] {
  border-color: var(--color-error);
}

.combobox-field__trigger:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.combobox-field__value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.combobox-field__value--placeholder,
.combobox-field__chevron {
  color: var(--color-on-surface-muted);
}

.combobox-field__chevron {
  flex: 0 0 auto;
}

.combobox-field__popover {
  position: absolute;
  z-index: 20;
  top: 100%;
  right: 0;
  left: 0;
  display: grid;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  padding: var(--space-sm);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-popover);
}

.combobox-field__search {
  width: 100%;
  min-height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  font: inherit;
}

.combobox-field__options {
  max-height: 220px;
  overflow-y: auto;
  margin: 0;
  padding: 0;
  list-style: none;
}

.combobox-field__option {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  color: var(--color-on-surface);
  cursor: pointer;
}

.combobox-field__option--active,
.combobox-field__option:hover:not(.combobox-field__option--disabled) {
  background: var(--color-surface-muted);
}

.combobox-field__option--disabled {
  color: var(--color-on-surface-muted);
  cursor: not-allowed;
}

.combobox-field__empty {
  padding: var(--space-sm) var(--space-md);
  color: var(--color-on-surface-muted);
}
</style>
