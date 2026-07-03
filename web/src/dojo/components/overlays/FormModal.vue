<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "reka-ui";

import Button from "@/dojo/components/actions/Button.vue";

withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    submitText?: string;
    cancelText?: string;
    dangerText?: string;
    submitDisabled?: boolean;
    loading?: boolean;
    contained?: boolean;
  }>(),
  {
    title: undefined,
    submitText: "Save",
    cancelText: "Cancel",
    dangerText: undefined,
    submitDisabled: false,
    loading: false,
    contained: false,
  },
);

const emit = defineEmits<{
  close: [];
  submit: [];
  cancel: [];
  danger: [];
}>();

const onOpenChange = (value: boolean) => {
  if (!value) {
    emit("close");
  }
};
</script>

<template>
  <DialogRoot :open="visible" :modal="!contained" @update:open="onOpenChange">
    <DialogPortal :disabled="contained">
      <div
        v-if="visible"
        class="modal-scrim"
        :class="{ 'modal-scrim--contained': contained }"
      >
        <DialogContent
          class="form-modal"
          data-cy="form-modal-root"
          @escape-key-down="emit('close')"
        >
          <header class="form-modal__header">
            <DialogTitle v-if="title" class="form-modal__title">{{
              title
            }}</DialogTitle>
            <slot name="header" />
            <DialogClose
              type="button"
              class="form-modal__close"
              aria-label="Close"
            >
              Close
            </DialogClose>
          </header>

          <div class="form-modal__body">
            <slot />
          </div>

          <footer class="form-modal__footer">
            <Button
              v-if="dangerText"
              variant="tertiary"
              @click="emit('danger')"
            >
              {{ dangerText }}
            </Button>
            <Button variant="secondary" @click="emit('cancel')">{{
              cancelText
            }}</Button>
            <Button
              :disabled="submitDisabled"
              :loading="loading"
              @click="emit('submit')"
            >
              {{ submitText }}
            </Button>
          </footer>
        </DialogContent>
      </div>
    </DialogPortal>
  </DialogRoot>
</template>

<style scoped>
.modal-scrim {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: var(--space-xl);
  background: var(--color-scrim);
  z-index: 200;
}

.modal-scrim--contained {
  position: relative;
  inset: auto;
  min-height: 320px;
  padding: var(--space-lg);
}

.form-modal {
  width: min(100%, 560px);
  max-height: min(760px, calc(100vh - var(--space-xl) * 2));
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-modal);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.form-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-xl) var(--space-xl) var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
}

.form-modal__close {
  flex-shrink: 0;
  min-width: 28px;
  min-height: 28px;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface-muted);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.form-modal__close:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.form-modal__title {
  margin: 0;
  max-width: 42ch;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.form-modal__body {
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-xl);
  overflow-y: auto;
}

.form-modal__footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-outline);
  background: var(--color-surface-raised);
}

.form-modal__footer > :first-child:last-of-type {
  margin-left: auto;
}

@media (max-width: 560px) {
  .modal-scrim {
    align-items: end;
    padding: var(--space-sm);
  }

  .form-modal {
    max-height: calc(100vh - var(--space-md));
  }

  .form-modal__header,
  .form-modal__body,
  .form-modal__footer {
    padding-left: var(--space-lg);
    padding-right: var(--space-lg);
  }

  .form-modal__footer {
    flex-wrap: wrap;
  }
}
</style>
