<script setup lang="ts">
import Button from "@/dojo/components/actions/Button.vue";

const props = withDefaults(
  defineProps<{
    severity?: "info" | "warning" | "error";
    title: string;
    description?: string;
    primaryAction?: string;
    secondaryAction?: string;
    dismissible?: boolean;
  }>(),
  {
    severity: "info",
    description: undefined,
    primaryAction: undefined,
    secondaryAction: undefined,
    dismissible: false,
  },
);

const emit = defineEmits<{
  primary: [];
  secondary: [];
  dismiss: [];
}>();

const severityIcon = (severity: "info" | "warning" | "error") => {
  if (severity === "warning") {
    return "!";
  }

  if (severity === "error") {
    return "x";
  }

  return "i";
};
</script>

<template>
  <div
    class="persistent-warning-banner"
    :class="`persistent-warning-banner--${severity}`"
    data-cy="persistent-warning-banner-root"
  >
    <span class="persistent-warning-banner__icon" aria-hidden="true">{{ severityIcon(props.severity) }}</span>
    <div class="persistent-warning-banner__copy">
      <p class="persistent-warning-banner__title">{{ title }}</p>
      <p v-if="description" class="persistent-warning-banner__description">{{ description }}</p>
    </div>
    <div v-if="primaryAction || secondaryAction || dismissible" class="persistent-warning-banner__actions">
      <Button
        v-if="secondaryAction"
        variant="tertiary"
        size="sm"
        @click="emit('secondary')"
      >
        {{ secondaryAction }}
      </Button>
      <Button
        v-if="primaryAction"
        variant="secondary"
        size="sm"
        @click="emit('primary')"
      >
        {{ primaryAction }}
      </Button>
      <button
        v-if="dismissible"
        type="button"
        class="persistent-warning-banner__dismiss"
        aria-label="Dismiss banner"
        @click="emit('dismiss')"
      >
        ×
      </button>
    </div>
  </div>
</template>

<style scoped>
.persistent-warning-banner {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: var(--space-md);
  padding: 10px 14px;
  border-radius: var(--radius-all);
}

.persistent-warning-banner--info {
  background: var(--color-info-container);
  color: var(--color-info);
}

.persistent-warning-banner--warning {
  background: var(--color-warning-container);
  color: var(--color-warning);
}

.persistent-warning-banner--error {
  background: var(--color-error-container);
  color: var(--color-error);
}

.persistent-warning-banner__icon {
  min-width: 16px;
  padding-top: 1px;
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: 700;
  line-height: 1;
  text-transform: uppercase;
}

.persistent-warning-banner__copy {
  display: grid;
  gap: var(--space-xs);
}

.persistent-warning-banner__title,
.persistent-warning-banner__description {
  margin: 0;
}

.persistent-warning-banner__title,
.persistent-warning-banner__description {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.persistent-warning-banner__title {
  font-weight: 600;
}

.persistent-warning-banner__actions {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-xs);
}

.persistent-warning-banner__dismiss {
  min-height: 28px;
  min-width: 28px;
  border: 1px solid currentColor;
  border-radius: var(--radius-all);
  background: transparent;
  color: currentColor;
  cursor: pointer;
}

@media (max-width: 639px) {
  .persistent-warning-banner {
    grid-template-columns: auto 1fr;
  }

  .persistent-warning-banner__actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}
</style>
