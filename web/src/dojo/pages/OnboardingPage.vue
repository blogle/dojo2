<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { useAppState } from "../state/app";

import Button from "../components/actions/Button.vue";
import TextField from "../components/forms/TextField.vue";
import LargeDetailModal from "../components/overlays/LargeDetailModal.vue";

const router = useRouter();
const { state, importSheet, beginGoogleOnboarding, initialize } = useAppState();

type Step = "choose" | "migrate-form" | "progress" | "complete" | "error";

const step = ref<Step>("choose");
const sheetId = ref("");
const errorMessage = ref("");

const importResult = computed(() => state.importResult);

async function handleStartEmpty() {
  await initialize();
  router.push("/budgets");
}

async function handleSubmitSheet() {
  if (!sheetId.value.trim()) return;
  step.value = "progress";
  errorMessage.value = "";

  try {
    await beginGoogleOnboarding();
    await importSheet(sheetId.value.trim());
    step.value = "complete";
  } catch (err) {
    errorMessage.value =
      err instanceof Error ? err.message : "Import failed. Please try again.";
    step.value = "error";
  }
}

function handleCancel() {
  step.value = "choose";
  sheetId.value = "";
  errorMessage.value = "";
}

function handleRetry() {
  step.value = "migrate-form";
  errorMessage.value = "";
}

function handleContinue() {
  router.push("/budgets");
}

const showDetails = ref(false);

const validationSummary = computed(() => {
  if (!importResult.value) return null;
  const r = importResult.value;
  return {
    ok: r.ok,
    errors: r.validation_report.hard_failures.length,
    warnings: r.validation_report.warnings.length,
  };
});
</script>

<template>
  <div class="onboarding" data-cy="onboarding-root">
    <div class="onboarding__card">
      <!-- Step: Choose path -->
      <template v-if="step === 'choose'">
        <h1 class="onboarding__title">dojo</h1>
        <p class="onboarding__subtitle">
          Your local-first personal finance app.
        </p>
        <p class="onboarding__description">
          Start with an empty budget, or import your existing data from a Google
          Aspire spreadsheet.
        </p>
        <div class="onboarding__actions">
          <Button variant="primary" @click="handleStartEmpty">
            Start empty
          </Button>
          <Button variant="secondary" @click="step = 'migrate-form'">
            Migrate from Aspire
          </Button>
        </div>
      </template>

      <!-- Step: Migration form -->
      <template v-if="step === 'migrate-form'">
        <h1 class="onboarding__title">Migrate from Aspire</h1>
        <p class="onboarding__description">
          Enter your Google Sheet ID to import data. dojo will request read
          access to the sheet.
        </p>
        <TextField
          v-model="sheetId"
          label="Google Sheet ID"
          placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
          helper="Found in the sheet URL between /d/ and /edit."
        />
        <div class="onboarding__actions">
          <Button
            variant="primary"
            :disabled="!sheetId.trim()"
            @click="handleSubmitSheet"
          >
            Submit
          </Button>
          <Button variant="secondary" @click="handleCancel"> Cancel </Button>
        </div>
      </template>

      <!-- Step: Progress -->
      <template v-if="step === 'progress'">
        <h1 class="onboarding__title">Importing data</h1>
        <p class="onboarding__description">
          Fetching and validating your Aspire spreadsheet. This may take a
          moment.
        </p>
        <div class="onboarding__spinner" />
      </template>

      <!-- Step: Complete -->
      <template v-if="step === 'complete'">
        <h1 class="onboarding__title">Import complete</h1>
        <p class="onboarding__description">
          Your data has been imported and validated successfully.
        </p>
        <div class="onboarding__actions">
          <Button variant="secondary" @click="showDetails = true">
            Details
          </Button>
          <Button variant="primary" @click="handleContinue">
            Continue to app
          </Button>
        </div>
      </template>

      <!-- Step: Error -->
      <template v-if="step === 'error'">
        <h1 class="onboarding__title">Import failed</h1>
        <p class="onboarding__description onboarding__description--error">
          {{ errorMessage }}
        </p>
        <div class="onboarding__actions">
          <Button variant="primary" @click="handleRetry"> Retry </Button>
          <Button variant="secondary" @click="handleCancel"> Cancel </Button>
        </div>
      </template>
    </div>

    <!-- Details modal -->
    <LargeDetailModal
      :visible="showDetails"
      title="Import details"
      @close="showDetails = false"
    >
      <div v-if="validationSummary" class="import-details">
        <div class="import-details__section">
          <h3 class="import-details__heading">Validation</h3>
          <p
            v-if="validationSummary.ok"
            class="import-details__status import-details__status--ok"
          >
            All checks passed
          </p>
          <p
            v-else
            class="import-details__status import-details__status--error"
          >
            Some checks failed ({{ validationSummary.errors }} error(s))
          </p>
          <p
            v-if="validationSummary.warnings > 0"
            class="import-details__warnings"
          >
            {{ validationSummary.warnings }} warning(s)
          </p>
        </div>
      </div>

      <template #footer>
        <Button variant="secondary" @click="showDetails = false">
          Close
        </Button>
      </template>
    </LargeDetailModal>
  </div>
</template>

<style scoped>
.onboarding {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: var(--space-xl);
  background: var(--color-background);
}

.onboarding__card {
  width: min(100%, 480px);
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-2xl);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
}

.onboarding__title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
}

.onboarding__subtitle {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.onboarding__description {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.onboarding__description--error {
  color: var(--color-error);
}

.onboarding__actions {
  display: flex;
  gap: var(--space-sm);
}

.onboarding__spinner {
  width: 32px;
  height: 32px;
  margin: var(--space-md) auto;
  border: 3px solid var(--color-outline);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.import-details {
  display: grid;
  gap: var(--space-lg);
}

.import-details__section {
  display: grid;
  gap: var(--space-sm);
}

.import-details__heading {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-title-sm-font-family);
  font-size: var(--text-title-sm-font-size);
  font-weight: var(--text-title-sm-font-weight);
}

.import-details__list {
  display: grid;
  gap: var(--space-xs);
}

.import-details__row {
  display: flex;
  justify-content: space-between;
}

.import-details__row dt {
  color: var(--color-on-surface-muted);
}

.import-details__row dd {
  margin: 0;
  color: var(--color-on-surface);
}

.import-details__status--ok {
  color: var(--color-positive);
}

.import-details__status--error {
  color: var(--color-error);
}

.import-details__warnings {
  color: var(--color-warning);
}
</style>
