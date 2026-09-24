<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, useId, watch } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    suggestions: string[];
    label: string;
    placeholder?: string;
    disabled?: boolean;
  }>(),
  {
    modelValue: "",
    placeholder: "Type a memo",
    disabled: false,
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const root = ref<HTMLElement | null>(null);
const input = ref<HTMLInputElement | null>(null);
const isOpen = ref(false);
const activeIndex = ref(-1);
const dismissedValue = ref<string | null>(null);
const id = useId();
const listId = `memo-suggestions-${id}`;
const inputId = `memo-input-${id}`;

const visibleSuggestions = computed(() => {
  const current = props.modelValue.trim().toLocaleLowerCase();
  return props.suggestions.filter(
    (suggestion) =>
      suggestion.trim() && suggestion.toLocaleLowerCase() !== current,
  );
});
const activeSuggestionId = computed(() =>
  activeIndex.value >= 0 ? `${listId}-option-${activeIndex.value}` : undefined,
);

watch(visibleSuggestions, (suggestions) => {
  if (document.activeElement === input.value) {
    isOpen.value =
      props.modelValue.trim().length >= 2 &&
      suggestions.length > 0 &&
      dismissedValue.value !== props.modelValue;
  }
  if (activeIndex.value >= suggestions.length) activeIndex.value = -1;
});

function handleInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  emit("update:modelValue", value);
  dismissedValue.value = null;
  activeIndex.value = -1;
  isOpen.value = value.trim().length >= 2;
}

function selectSuggestion(suggestion: string) {
  emit("update:modelValue", suggestion);
  dismissedValue.value = suggestion;
  isOpen.value = false;
  activeIndex.value = -1;
  input.value?.focus();
}

function moveActiveSuggestion(direction: -1 | 1) {
  if (!visibleSuggestions.value.length) return;
  activeIndex.value =
    (activeIndex.value + direction + visibleSuggestions.value.length) %
    visibleSuggestions.value.length;
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    if (visibleSuggestions.value.length) {
      event.preventDefault();
      isOpen.value = true;
      moveActiveSuggestion(event.key === "ArrowDown" ? 1 : -1);
    }
  } else if (event.key === "Enter") {
    const suggestion = visibleSuggestions.value[activeIndex.value];
    if (isOpen.value && suggestion) {
      event.preventDefault();
      selectSuggestion(suggestion);
    }
  } else if (event.key === "Escape" && isOpen.value) {
    event.preventDefault();
    isOpen.value = false;
    activeIndex.value = -1;
    dismissedValue.value = props.modelValue;
  } else if (event.key === "Tab") {
    isOpen.value = false;
  }
}

function handleOutsidePointer(event: PointerEvent) {
  if (!root.value?.contains(event.target as Node)) {
    isOpen.value = false;
    activeIndex.value = -1;
    dismissedValue.value = props.modelValue;
  }
}

onMounted(() => document.addEventListener("pointerdown", handleOutsidePointer));
onUnmounted(() =>
  document.removeEventListener("pointerdown", handleOutsidePointer),
);
</script>

<template>
  <div ref="root" class="memo-autocomplete" data-cy="memo-autocomplete-field">
    <label class="memo-autocomplete__label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      ref="input"
      class="memo-autocomplete__input"
      data-cy="memo-autocomplete-input"
      type="text"
      role="combobox"
      aria-autocomplete="list"
      aria-haspopup="listbox"
      :aria-expanded="isOpen && visibleSuggestions.length > 0"
      :aria-controls="listId"
      :aria-activedescendant="activeSuggestionId"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      autocomplete="off"
      @input="handleInput"
      @focus="
        dismissedValue = null;
        isOpen = modelValue.trim().length >= 2 && visibleSuggestions.length > 0;
      "
      @keydown="handleKeydown"
    />
    <ul
      v-if="isOpen && visibleSuggestions.length"
      :id="listId"
      class="memo-autocomplete__suggestions"
      role="listbox"
      :aria-label="`${label} suggestions`"
    >
      <li
        v-for="(suggestion, index) in visibleSuggestions"
        :id="`${listId}-option-${index}`"
        :key="suggestion"
        class="memo-autocomplete__suggestion"
        :class="{
          'memo-autocomplete__suggestion--active': activeIndex === index,
        }"
        role="option"
        :aria-selected="suggestion === modelValue"
        @pointerdown.prevent
        @click="selectSuggestion(suggestion)"
      >
        {{ suggestion }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.memo-autocomplete {
  position: relative;
  display: grid;
  gap: var(--space-xs);
  min-width: 0;
}

.memo-autocomplete__label {
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-on-surface-muted);
}

.memo-autocomplete__input {
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
}

.memo-autocomplete__input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.memo-autocomplete__input:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.memo-autocomplete__suggestions {
  position: absolute;
  z-index: 20;
  top: 100%;
  right: 0;
  left: 0;
  max-height: 220px;
  overflow-y: auto;
  margin: var(--space-xs) 0 0;
  padding: var(--space-xs);
  list-style: none;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-popover);
}

.memo-autocomplete__suggestion {
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  color: var(--color-on-surface);
  cursor: pointer;
}

.memo-autocomplete__suggestion--active,
.memo-autocomplete__suggestion:hover {
  background: var(--color-surface-muted);
}
</style>
