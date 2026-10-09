<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";

import { useMutationFeedback } from "../state/mutationFeedback";

const {
  notice,
  undoPending,
  confirmationPending,
  dismiss,
  undoLatest,
  confirmChange,
} = useMutationFeedback();

function handleKeydown(event: KeyboardEvent): void {
  if (!(event.metaKey || event.ctrlKey) || event.key.toLowerCase() !== "z")
    return;
  const target = event.target;
  if (
    target instanceof HTMLElement &&
    target.closest("input, textarea, select, [contenteditable='true']")
  ) {
    return;
  }
  if (!notice.value?.undoId) return;
  event.preventDefault();
  void undoLatest();
}

onMounted(() => document.addEventListener("keydown", handleKeydown));
onBeforeUnmount(() => document.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <Transition name="mutation-feedback">
    <div
      v-if="notice"
      class="mutation-feedback"
      :class="`mutation-feedback--${notice.kind}`"
      :role="notice.kind === 'error' ? 'alert' : 'status'"
      :aria-live="notice.kind === 'error' ? 'assertive' : 'polite'"
      aria-atomic="true"
      data-cy="mutation-feedback"
    >
      <span class="mutation-feedback__message">{{ notice.message }}</span>
      <button
        v-if="notice.confirm"
        class="mutation-feedback__confirm"
        type="button"
        :disabled="confirmationPending"
        @click="confirmChange"
      >
        {{ confirmationPending ? "Applying…" : "Apply anyway" }}
      </button>
      <button
        v-if="notice.cancel"
        class="mutation-feedback__cancel"
        type="button"
        :disabled="confirmationPending"
        @click="dismiss"
      >
        Cancel
      </button>
      <button
        v-if="notice.undoId"
        class="mutation-feedback__undo"
        type="button"
        :disabled="undoPending"
        @click="undoLatest"
      >
        {{ notice.undoLabel ?? "Undo" }}
      </button>
      <button
        class="mutation-feedback__dismiss"
        type="button"
        aria-label="Dismiss notification"
        :disabled="confirmationPending"
        @click="dismiss"
      >
        ×
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.mutation-feedback {
  position: fixed;
  right: var(--space-xl);
  bottom: var(--space-xl);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: var(--space-md);
  max-width: 380px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-on-surface);
  color: var(--color-surface);
  box-shadow: var(--shadow-popover);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.mutation-feedback--error {
  background: var(--color-error);
  color: var(--color-on-primary);
}

.mutation-feedback--success {
  background: var(--color-positive);
  color: var(--color-on-primary);
}

.mutation-feedback__message {
  flex: 1;
}

.mutation-feedback button {
  border: 0;
  padding: var(--space-xs);
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.mutation-feedback__undo,
.mutation-feedback__confirm,
.mutation-feedback__cancel {
  font-family: var(--text-label-sm-font-family) !important;
  font-size: var(--text-label-sm-font-size) !important;
  font-weight: 600 !important;
  text-decoration: underline !important;
  text-underline-offset: var(--space-micro);
}

.mutation-feedback__dismiss {
  font-size: var(--text-headline-sm-font-size) !important;
}

.mutation-feedback button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.mutation-feedback button:focus-visible {
  border-radius: var(--radius-all);
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

.mutation-feedback-enter-active,
.mutation-feedback-leave-active {
  transition:
    opacity var(--transition-normal) var(--transition-ease-out),
    transform var(--transition-normal) var(--transition-ease-out);
}

.mutation-feedback-enter-from,
.mutation-feedback-leave-to {
  opacity: 0;
  transform: translateX(var(--space-md));
}
</style>
