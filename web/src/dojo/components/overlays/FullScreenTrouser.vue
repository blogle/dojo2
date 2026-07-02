<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { useDismissableLayer } from "@/dojo/composables/useDismissableLayer";

const props = withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    subtitle?: string;
  }>(),
  {
    title: undefined,
    subtitle: undefined,
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
  <Teleport to="body">
    <div
      v-if="visible"
      class="trouser-scrim"
      data-cy="full-screen-trouser-root"
    >
      <section
        ref="panel"
        class="trouser"
        tabindex="-1"
        role="dialog"
        aria-modal="true"
      >
        <header class="trouser__header">
          <div class="trouser__header-copy">
            <h2 v-if="title || $slots.title" class="trouser__title">
              <slot name="title">{{ title }}</slot>
            </h2>
            <p v-if="subtitle || $slots.subtitle" class="trouser__subtitle">
              <slot name="subtitle">{{ subtitle }}</slot>
            </p>
          </div>
          <div class="trouser__header-actions">
            <slot name="header-actions" />
          </div>
          <button
            type="button"
            class="trouser__close"
            aria-label="Close"
            @click="emit('close')"
          >
            ×
          </button>
        </header>

        <div v-if="$slots.tabs" class="trouser__tabs">
          <slot name="tabs" />
        </div>

        <div class="trouser__body">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="trouser__footer">
          <slot name="footer" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.trouser-scrim {
  position: fixed;
  inset: 0;
  background: var(--color-scrim);
  z-index: 200;
}

.trouser {
  position: absolute;
  inset: 0;
  left: auto;
  width: min(100%, 960px);
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--color-outline);
  background: var(--color-surface-raised);
  box-shadow: var(--shadow-modal);
  overflow: hidden;
}

.trouser__header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-raised);
  flex-shrink: 0;
}

.trouser__header-copy {
  display: grid;
  gap: var(--space-xs);
  flex: 1;
  min-width: 0;
}

.trouser__header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.trouser__title,
.trouser__subtitle {
  margin: 0;
}

.trouser__title {
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.trouser__subtitle {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.trouser__close {
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

.trouser__close:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.trouser__tabs {
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--color-outline);
  flex-shrink: 0;
}

.trouser__body {
  flex: 1;
  overflow-y: auto;
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-xl);
  align-content: start;
}

.trouser__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-lg) var(--space-xl);
  border-top: 1px solid var(--color-outline);
  flex-shrink: 0;
}
</style>
