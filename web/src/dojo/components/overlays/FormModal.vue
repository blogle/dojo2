<script setup lang="ts">
import { computed, ref, watch } from "vue";

import Button from "@/dojo/components/actions/Button.vue";
import { useDismissableLayer } from "@/dojo/composables/useDismissableLayer";

const props = withDefaults(
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

const panel = ref<HTMLElement | null>(null);
const active = computed(() => props.visible);

useDismissableLayer(active, panel, () => emit("close"));

watch(
  () => props.visible,
  (visible) => {
    if (!visible) {
      return;
    }

    requestAnimationFrame(() => panel.value?.focus());
  },
);
</script>

<template>
  <Teleport to="body" :disabled="contained">
    <div
      v-if="visible"
      class="modal-scrim"
      :class="{ 'modal-scrim--contained': contained }"
      data-cy="form-modal-root"
    >
      <section
        ref="panel"
        class="form-modal"
        tabindex="-1"
        role="dialog"
        aria-modal="true"
      >
        <header class="form-modal__header">
          <h2 v-if="title" class="form-modal__title">{{ title }}</h2>
          <slot name="header" />
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
          <Button variant="secondary" @click="emit('cancel')">{{ cancelText }}</Button>
          <Button
            :disabled="submitDisabled"
            :loading="loading"
            @click="emit('submit')"
          >
            {{ submitText }}
          </Button>
        </footer>
      </section>
    </div>
  </Teleport>
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
  width: min(100%, 480px);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-modal);
}

.form-modal__header {
  display: grid;
  gap: var(--space-xs);
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--color-outline);
}

.form-modal__title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.form-modal__body {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-xl);
}

.form-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-outline);
}
</style>
