<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
    subtitle?: string;
    eyebrow?: string;
    metadata?: string;
    primaryActions?: boolean;
    sticky?: boolean;
  }>(),
  {
    title: "",
    subtitle: undefined,
    eyebrow: undefined,
    metadata: undefined,
    primaryActions: false,
    sticky: false,
  },
);
</script>

<template>
  <header
    class="page-header"
    :class="{ 'page-header--sticky': sticky }"
    data-cy="page-header-root"
  >
    <div class="page-header__top-row">
      <div class="page-header__copy">
        <p v-if="eyebrow || $slots.eyebrow" class="page-header__eyebrow">
          <slot name="eyebrow">{{ eyebrow }}</slot>
        </p>
        <h1 class="page-header__title">
          <slot name="title">{{ title }}</slot>
        </h1>
        <p v-if="subtitle || $slots.subtitle" class="page-header__subtitle">
          <slot name="subtitle">{{ subtitle }}</slot>
        </p>
      </div>

      <div
        v-if="$slots.actions"
        class="page-header__actions"
        :class="{ 'page-header__actions--primary': primaryActions }"
      >
        <slot name="actions" />
      </div>
    </div>

    <p v-if="metadata || $slots.metadata" class="page-header__metadata">
      <slot name="metadata">{{ metadata }}</slot>
    </p>

    <div v-if="$slots.tabs" class="page-header__tabs">
      <slot name="tabs" />
    </div>

    <div v-if="$slots.default" class="page-header__body">
      <slot />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: grid;
  gap: var(--space-sm);
  padding: 0 0 var(--space-lg);
  margin: 0 0 var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-background);
}

.page-header--sticky {
  position: sticky;
  top: 0;
  z-index: 10;
}

.page-header__top-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
}

.page-header__copy,
.page-header__actions,
.page-header__tabs,
.page-header__body {
  min-width: 0;
}

.page-header__copy {
  display: grid;
  gap: var(--space-xs);
}

.page-header__eyebrow,
.page-header__title,
.page-header__subtitle,
.page-header__metadata {
  margin: 0;
}

.page-header__eyebrow {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.page-header__title {
  color: var(--color-on-surface);
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
  letter-spacing: var(--text-headline-lg-letter-spacing);
}

.page-header__subtitle,
.page-header__metadata {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.page-header__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-sm);
}

.page-header__actions--primary {
  align-items: center;
}

.page-header__tabs,
.page-header__body {
  display: grid;
  gap: var(--space-sm);
}

@media (max-width: 639px) {
  .page-header__top-row {
    flex-direction: column;
  }

  .page-header__actions {
    width: 100%;
    justify-content: stretch;
  }

  .page-header__actions :deep(*) {
    flex: 1 1 auto;
  }
}
</style>
