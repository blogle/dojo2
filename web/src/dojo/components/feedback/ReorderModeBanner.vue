<script setup lang="ts">
withDefaults(
  defineProps<{
    pendingCount?: number;
    cancelText?: string;
    saveText?: string;
  }>(),
  {
    pendingCount: 0,
    cancelText: "Cancel",
    saveText: "Save",
  },
);

const emit = defineEmits<{
  cancel: [];
  save: [];
}>();
</script>

<template>
  <div class="reorder-banner" data-cy="reorder-mode-banner-root">
    <div class="reorder-banner__label">
      <span>Reordering mode</span>
      <span v-if="pendingCount > 0" class="reorder-banner__pending">
        &bull; {{ pendingCount }} changes pending
      </span>
    </div>
    <div class="reorder-banner__actions">
      <button
        type="button"
        class="reorder-banner__cancel"
        @click="emit('cancel')"
      >
        {{ cancelText }}
      </button>
      <button type="button" class="reorder-banner__save" @click="emit('save')">
        {{ saveText }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.reorder-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-primary-container);
  border-radius: var(--radius-all);
}

.reorder-banner__label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
  color: var(--color-on-primary-container);
}

.reorder-banner__pending {
  color: var(--color-on-primary-container);
  opacity: 0.8;
}

.reorder-banner__actions {
  display: flex;
  gap: var(--space-sm);
}

.reorder-banner__cancel {
  appearance: none;
  padding: 0 var(--space-md);
  min-height: 28px;
  border: 1px solid transparent;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-primary-container);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
  cursor: pointer;
}

.reorder-banner__cancel:hover {
  background: color-mix(
    in srgb,
    var(--color-on-primary-container) 8%,
    transparent
  );
}

.reorder-banner__save {
  appearance: none;
  padding: 0 var(--space-md);
  min-height: 28px;
  border: 1px solid transparent;
  border-radius: var(--radius-all);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
  cursor: pointer;
}

.reorder-banner__save:hover {
  background: var(--color-primary-hover);
}
</style>
