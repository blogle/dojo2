<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppState } from "./state/app";

const router = useRouter();
const { initialize, ready } = useAppState();

onMounted(async () => {
  await initialize();
  if (!ready.value) {
    router.replace("/onboarding");
  }
});
</script>

<template>
  <router-view />
</template>
