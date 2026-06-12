<script setup lang="ts">
import { onMounted } from "vue";

import { useAppState } from "../state/app";
import ErrorBanner from "./ErrorBanner.vue";
import TopNav from "./TopNav.vue";

const app = useAppState();

onMounted(async () => {
  if (!app.state.bootstrap) {
    await app.initialize();
  }
});
</script>

<template>
  <main class="shell">
    <div class="inner-shell">
      <TopNav :ready="app.ready.value" />
      <ErrorBanner v-if="app.state.error" :message="app.state.error" />
      <slot />
    </div>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 1.5rem;
}

.inner-shell {
  max-width: 96rem;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}
</style>
