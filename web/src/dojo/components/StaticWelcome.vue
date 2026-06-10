<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { fetchAppStatus, type AppStatus } from "../api/client";

const status = ref<"loading" | "reachable" | "unreachable">("loading");
const details = ref<AppStatus | null>(null);

const statusText = computed(() => {
  if (status.value === "loading") {
    return "Checking API reachability...";
  }

  if (status.value === "reachable") {
    return `API reachable: ${details.value?.mode ?? "skeleton"} mode`;
  }

  return "API unreachable.";
});

onMounted(async () => {
  try {
    details.value = await fetchAppStatus();
    status.value = "reachable";
  } catch {
    status.value = "unreachable";
  }
});
</script>

<template>
  <article class="welcome">
    <p class="eyebrow">local-first personal finance</p>
    <h1>dojo</h1>
    <p class="lead">Project skeleton is running.</p>
    <div class="status-card" :data-status="status">
      <p class="label">API status</p>
      <p class="value">
        {{ statusText }}
      </p>
    </div>
  </article>
</template>

<style scoped>
.welcome {
  display: grid;
  gap: 1rem;
}

.eyebrow {
  margin: 0;
  color: var(--dojo-green-dark);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--dojo-text-dark-brown);
  font-size: clamp(2.8rem, 10vw, 5rem);
  line-height: 0.95;
}

.lead {
  margin: 0;
  color: var(--dojo-text-soft-brown);
  font-size: 1.1rem;
}

.status-card {
  border: 1px solid var(--dojo-border-brown);
  border-radius: 18px;
  padding: 1rem 1.25rem;
  background: rgba(236, 229, 216, 0.85);
}

.status-card[data-status="reachable"] {
  border-color: var(--dojo-green-muted);
}

.label {
  margin: 0 0 0.35rem;
  color: var(--dojo-text-soft-brown);
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
}

.value {
  margin: 0;
  color: var(--dojo-text-dark-brown);
}
</style>
