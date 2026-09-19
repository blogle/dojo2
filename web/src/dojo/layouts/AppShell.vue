<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import NavigationRail from "../components/navigation/NavigationRail.vue";
import type { NavigationRailItem } from "../components/navigation/NavigationRail.vue";
import PersistentWarningBanner from "../components/feedback/PersistentWarningBanner.vue";
import { ApiError, fetchAppStatus, requestBackupRun } from "../api/client";
import {
  readNavigationExpanded,
  writeNavigationExpanded,
} from "../state/navigation";
import { useAppState } from "../state/app";

const route = useRoute();
const router = useRouter();
const { state, ready } = useAppState();
const railExpanded = ref(readNavigationExpanded());
const retryQueued = ref(false);
const retryError = ref("");
let retryStatusTimer: number | undefined;

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

const backupAction = computed(
  () => state.appStatus?.backup?.action ?? "repair",
);
const backupDescription = computed(
  () =>
    retryError.value ||
    (retryQueued.value
      ? "A backup retry was queued. This warning will clear after it succeeds."
      : (state.appStatus?.backup.message ??
        "Set up or repair Google Drive backups so your data has an off-site recovery copy.")),
);

function handleRailToggle(expanded: boolean): void {
  railExpanded.value = expanded;
  writeNavigationExpanded(expanded);
}

function repairBackups(): void {
  router.push({ path: "/onboarding", query: { backup: "repair" } });
}

function handlePrimaryBackupAction(): void {
  if (backupAction.value === "retry") {
    void retryBackups();
    return;
  }
  repairBackups();
}

async function retryBackups(): Promise<void> {
  retryError.value = "";
  try {
    await requestBackupRun();
    retryQueued.value = true;
    scheduleRetryStatusRefresh();
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.code === "google_drive_reauthorization_required"
    ) {
      repairBackups();
      return;
    }
    retryError.value =
      error instanceof Error
        ? error.message
        : "Backup retry could not be queued.";
  }
}

function scheduleRetryStatusRefresh(): void {
  if (retryStatusTimer !== undefined) {
    window.clearTimeout(retryStatusTimer);
  }
  retryStatusTimer = window.setTimeout(() => {
    void refreshRetryStatus();
  }, 2000);
}

async function refreshRetryStatus(): Promise<void> {
  if (!retryQueued.value) return;
  try {
    state.appStatus = await fetchAppStatus();
    if (
      state.appStatus.backup.state === "configured" ||
      state.appStatus.backup.action === "retry"
    ) {
      retryQueued.value = false;
      return;
    }
  } catch {
    // Keep the queued state while the backup worker is unavailable.
  }
  scheduleRetryStatusRefresh();
}

onBeforeUnmount(() => {
  if (retryStatusTimer !== undefined) {
    window.clearTimeout(retryStatusTimer);
  }
});
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
        :description="backupDescription"
        :primary-action="
          retryQueued
            ? undefined
            : backupAction === 'retry'
              ? 'Retry backup'
              : 'Repair backups'
        "
        :secondary-action="
          retryQueued || backupAction !== 'retry' ? undefined : 'Repair backups'
        "
        @primary="handlePrimaryBackupAction"
        @secondary="repairBackups"
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
