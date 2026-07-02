<script setup lang="ts">
import Button from "@/dojo/components/actions/Button.vue";

withDefaults(
  defineProps<{
    label?: string;
    description?: string;
    exitLabel?: string;
  }>(),
  {
    label: "Viewing historical data",
    description: undefined,
    exitLabel: "Return to current",
  },
);

const emit = defineEmits<{
  exit: [];
}>();
</script>

<template>
  <div class="historical-banner" data-cy="historical-banner-root">
    <div class="historical-banner__copy">
      <p class="historical-banner__label">{{ label }}</p>
      <p v-if="description" class="historical-banner__description">
        {{ description }}
      </p>
    </div>
    <Button variant="primary" size="sm" @click="emit('exit')">{{
      exitLabel
    }}</Button>
  </div>
</template>

<style scoped>
.historical-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: 8px 12px;
  border-radius: var(--radius-all);
  background: var(--color-historical-container);
  color: var(--color-historical);
}

.historical-banner__copy {
  display: grid;
  gap: var(--space-xs);
}

.historical-banner__label,
.historical-banner__description {
  margin: 0;
}

.historical-banner__label {
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.historical-banner__description {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

@media (max-width: 639px) {
  .historical-banner {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
