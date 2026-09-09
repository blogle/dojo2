<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAppState } from "./state/app";
import PersistentWarningBanner from "./components/feedback/PersistentWarningBanner.vue";

const router = useRouter();
const route = useRoute();
const { state, initialize, ready } = useAppState();
const showBackupWarning = computed(
  () => ready.value && state.appStatus?.backup?.state === "degraded",
);

onMounted(async () => {
  if (route.path.startsWith("/dev/")) return;
  await initialize();
  if (!ready.value) {
    router.replace("/onboarding");
  }
});

function repairBackups() {
  router.push({ path: "/onboarding", query: { backup: "repair" } });
}
</script>

<template>
  <PersistentWarningBanner
    v-if="showBackupWarning"
    severity="warning"
    title="Backups need attention"
    :description="
      state.appStatus?.backup.message ??
      'Set up or repair Google Drive backups so your data has an off-site recovery copy.'
    "
    primary-action="Repair backups"
    @primary="repairBackups"
  />
  <router-view />
</template>
