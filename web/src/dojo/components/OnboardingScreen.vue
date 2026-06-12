<script setup lang="ts">
import { computed, ref } from "vue";

import type { ImportResult } from "../types";
import GoogleAccessStep from "./GoogleAccessStep.vue";
import ImportConfirmStep from "./ImportConfirmStep.vue";
import ImportPreview from "./ImportPreview.vue";
import ImportValidationReport from "./ImportValidationReport.vue";
import Panel from "./Panel.vue";
import SheetIdInput from "./SheetIdInput.vue";

const props = defineProps<{
  loading: boolean;
  onboardingInfo: Record<string, unknown> | null;
  importResult: ImportResult | null;
}>();

const emit = defineEmits<{ beginGoogle: []; importSheet: [sheetId: string] }>();
const sheetInput = ref("fixture://default");
const configured = computed(() => Boolean(props.onboardingInfo?.configured));
const fixtureMode = computed(() => Boolean(props.onboardingInfo?.fixture_mode));
const authorized = computed(() => Boolean(props.onboardingInfo?.authorized));
</script>

<template>
  <div class="onboarding-screen">
    <Panel>
      <h1>Dojo onboarding</h1>
      <p>Import the copied spreadsheet once, validate the numbers to the penny, then budget locally in DuckDB.</p>
    </Panel>
    <Panel>
      <GoogleAccessStep :authorized="authorized" :configured="configured" :fixture-mode="fixtureMode" :loading="loading" @begin="emit('beginGoogle')" />
      <SheetIdInput v-model="sheetInput" />
      <ImportPreview title="Copy of Finances 2.0" :summary="importResult?.validation_report.summary ?? null" />
      <ImportConfirmStep :loading="loading" @confirm="emit('importSheet', sheetInput)" />
      <ImportValidationReport :report="importResult?.validation_report ?? null" />
    </Panel>
  </div>
</template>

<style scoped>
.onboarding-screen {
  display: grid;
  gap: 1rem;
}

h1,
p {
  margin: 0;
}
</style>
