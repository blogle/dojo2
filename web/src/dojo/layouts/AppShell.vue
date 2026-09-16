<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import NavigationRail from "../components/navigation/NavigationRail.vue";
import type { NavigationRailItem } from "../components/navigation/NavigationRail.vue";
import PersistentWarningBanner from "../components/feedback/PersistentWarningBanner.vue";
import {
  readNavigationExpanded,
  writeNavigationExpanded,
} from "../state/navigation";
import { useAppState } from "../state/app";

const route = useRoute();
const router = useRouter();
const { state, ready } = useAppState();
const railExpanded = ref(readNavigationExpanded());

const primaryItems = computed<NavigationRailItem[]>(() => [
  {
    kind: "route",
    key: "home",
    label: "Dashboard",
    icon: "dashboard",
    href: "/",
    current: false,
  },
  {
    kind: "route",
    key: "budget",
    label: "Budget",
    icon: "budget",
    href: "/budgets",
    current: route.path === "/" || route.path.startsWith("/budgets"),
  },
  {
    kind: "route",
    key: "transactions",
    label: "Transactions",
    icon: "transactions",
    href: "/transactions",
    current: route.path.startsWith("/transactions"),
  },
  {
    kind: "route",
    key: "assets-liabilities",
    label: "Assets & Liabilities",
    icon: "assets",
    href: "/assets-liabilities",
    current: route.path.startsWith("/assets-liabilities"),
  },
]);

const showBackupWarning = computed(
  () => ready.value && state.appStatus?.backup?.state === "degraded",
);

function handleRailToggle(expanded: boolean): void {
  railExpanded.value = expanded;
  writeNavigationExpanded(expanded);
}

function repairBackups(): void {
  router.push({ path: "/onboarding", query: { backup: "repair" } });
}
</script>

<template>
  <div
    class="app-shell"
    :class="{ 'app-shell--expanded': railExpanded }"
    data-cy="app-shell"
  >
    <NavigationRail
      :primary-items="primaryItems"
      :expanded="railExpanded"
      brand="dojo"
      aria-label="Main navigation"
      @toggle="handleRailToggle"
    />

    <main class="app-shell__content" data-cy="app-shell-content">
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
      <div class="app-shell__page">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: var(--space-nav-collapsed) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--color-background);
}

.app-shell--expanded {
  grid-template-columns: var(--space-nav-expanded) minmax(0, 1fr);
}

.app-shell__content {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.app-shell__page {
  min-width: 0;
  flex: 1;
}
</style>
