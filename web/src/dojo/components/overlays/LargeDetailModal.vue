<script setup lang="ts">
import { computed, ref, watch } from "vue";

import Button from "@/dojo/components/actions/Button.vue";
import { useDismissableLayer } from "@/dojo/composables/useDismissableLayer";

const props = withDefaults(
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
      data-cy="large-detail-modal-root"
    >
      <section
        ref="panel"
        class="large-detail-modal"
        tabindex="-1"
        role="dialog"
        aria-modal="true"
      >
        <header
          class="large-detail-modal__header"
          :class="{ 'large-detail-modal__header--sticky': sticky }"
        >
          <div class="large-detail-modal__header-copy">
            <h2 v-if="title || $slots.title" class="large-detail-modal__title">
              <slot name="title">{{ title }}</slot>
            </h2>
            <p
              v-if="subtitle || $slots.subtitle"
              class="large-detail-modal__subtitle"
            >
              <slot name="subtitle">{{ subtitle }}</slot>
            </p>
          </div>
          <Button variant="tertiary" size="sm" @click="emit('close')">Close</Button>
        </header>

        <div v-if="$slots.tabs" class="large-detail-modal__tabs">
          <slot name="tabs" />
        </div>

        <div class="large-detail-modal__body">
          <slot />
        </div>

        <footer v-if="$slots.footer || $slots.actions" class="large-detail-modal__footer">
          <slot name="footer">
            <slot name="actions" />
          </slot>
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
  min-height: 520px;
  padding: var(--space-lg);
}

.large-detail-modal {
  width: min(100%, 900px);
  max-height: 80vh;
  overflow: auto;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
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
