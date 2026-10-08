<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAppState } from "./state/app";
import MutationFeedbackHost from "./layouts/MutationFeedbackHost.vue";

const router = useRouter();
const route = useRoute();
const { initialize, ready } = useAppState();

onMounted(async () => {
  if (route.path.startsWith("/dev/")) return;
  await initialize();
  if (!ready.value) {
    router.replace("/onboarding");
  }
});
</script>

<template>
  <router-view />
  <MutationFeedbackHost />
</template>
