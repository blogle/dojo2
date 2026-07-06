<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAppState } from "./state/app";

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
</template>
