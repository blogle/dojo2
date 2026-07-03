<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "reka-ui";

withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    subtitle?: string;
    sticky?: boolean;
    contained?: boolean;
  }>(),
  {
    title: undefined,
    subtitle: undefined,
    sticky: false,
    contained: false,
  },
);

const emit = defineEmits<{
  close: [];
}>();
</script>

<template>
  <DialogRoot
    :open="visible"
    :modal="!contained"
    @update:open="(open) => !open && emit('close')"
  >
    <DialogPortal :disabled="contained">
      <div
        v-if="visible"
        class="modal-scrim"
        :class="{ 'modal-scrim--contained': contained }"
      >
        <DialogContent
          class="large-detail-modal"
          data-cy="large-detail-modal-root"
          @escape-key-down="emit('close')"
          @open-auto-focus.prevent
        >
          <header
            class="large-detail-modal__header"
            :class="{ 'large-detail-modal__header--sticky': sticky }"
          >
            <div class="large-detail-modal__header-copy">
              <DialogTitle
                v-if="title || $slots.title"
                class="large-detail-modal__title"
                as="h2"
              >
                <slot name="title">{{ title }}</slot>
              </DialogTitle>
              <DialogDescription
                v-if="subtitle || $slots.subtitle"
                class="large-detail-modal__subtitle"
              >
                <slot name="subtitle">{{ subtitle }}</slot>
              </DialogDescription>
            </div>
            <DialogClose
              type="button"
              class="large-detail-modal__close"
              aria-label="Close"
            >
              Close
            </DialogClose>
          </header>

          <div v-if="$slots.tabs" class="large-detail-modal__tabs">
            <slot name="tabs" />
          </div>

          <div class="large-detail-modal__body">
            <slot />
          </div>

          <footer
            v-if="$slots.footer || $slots.actions"
            class="large-detail-modal__footer"
          >
            <slot name="footer">
              <slot name="actions" />
            </slot>
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
  min-height: 520px;
  padding: var(--space-lg);
}

.large-detail-modal {
  width: min(100%, 900px);
  max-height: 80vh;
  overflow: auto;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-modal);
}

.large-detail-modal__header,
.large-detail-modal__tabs,
.large-detail-modal__footer {
  padding-left: var(--space-xl);
  padding-right: var(--space-xl);
}

.large-detail-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
  padding-top: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-raised);
}

.large-detail-modal__header--sticky {
  position: sticky;
  top: 0;
  z-index: 1;
}

.large-detail-modal__header-copy {
  display: grid;
  gap: var(--space-xs);
}

.large-detail-modal__title,
.large-detail-modal__subtitle {
  margin: 0;
}

.large-detail-modal__title {
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.large-detail-modal__subtitle {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.large-detail-modal__close {
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

.large-detail-modal__close:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.large-detail-modal__tabs {
  padding-top: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-outline);
}

.large-detail-modal__body {
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-xl);
}

.large-detail-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding-top: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-top: 1px solid var(--color-outline);
}
</style>
