<template>
  <div class="loading-skeleton">
    <div v-for="item in 4" :key="item" class="bar" />
  </div>
</template>

<style scoped>
.loading-skeleton {
  display: grid;
  gap: 0.5rem;
}

.bar {
  height: 1rem;
  background: var(--dojo-bg-muted-sand);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}
</style>
