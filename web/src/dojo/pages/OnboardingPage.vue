<script setup lang="ts">
import {
  PhArrowLeft,
  PhArrowSquareOut,
  PhCheck,
  PhFileText,
  PhInfo,
  PhTable,
  PhWarningCircle,
} from "@phosphor-icons/vue";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { useAppState } from "../state/app";

import Button from "../components/actions/Button.vue";
import TextField from "../components/forms/TextField.vue";
import Surface from "../components/layout/Surface.vue";
import Inline from "../components/layout/Inline.vue";
import Divider from "../components/layout/Divider.vue";
import ProgressBar from "../components/display/ProgressBar.vue";
import StatusStepList from "../components/feedback/StatusStepList.vue";
import type { StatusStep } from "../components/feedback/StatusStepList.vue";
import ImportDetailsModal from "./onboarding/ImportDetailsModal.vue";

const router = useRouter();
const { state, importSheet, beginGoogleOnboarding, initialize } = useAppState();

type Step = "choose" | "migrate-form" | "progress" | "complete";

const step = ref<Step>("choose");
const sheetId = ref("");
const errorMessage = ref("");
const formError = ref("");

const importResult = computed(() => state.importResult);

async function handleStartEmpty() {
  await initialize();
  router.push("/budgets");
}

async function handleSubmitSheet() {
  if (!sheetId.value.trim()) return;
  step.value = "progress";
  errorMessage.value = "";
  formError.value = "";

  try {
    await beginGoogleOnboarding();
    await importSheet(sheetId.value.trim());
    step.value = "complete";
  } catch (err) {
    errorMessage.value =
      err instanceof Error ? err.message : "Import failed. Please try again.";
    step.value = "migrate-form";
  }
}

function handleCancel() {
  step.value = "choose";
  sheetId.value = "";
  errorMessage.value = "";
  formError.value = "";
}

function handleBack() {
  step.value = "choose";
  errorMessage.value = "";
  formError.value = "";
}

function handleContinue() {
  router.push("/budgets");
}

const showDetails = ref(false);

const progressPercent = ref(68);
const progressLabel = ref("Importing records (2,746 of 4,032)");

const statusSteps = ref<StatusStep[]>([
  {
    title: "Reading Google Sheet",
    description: "Connected and read 4,032 rows.",
    status: "complete",
  },
  {
    title: "Importing records",
    description: "Importing budgets, actuals, and related data.",
    status: "in-progress",
  },
  {
    title: "Validating records",
    description: "Checking data integrity and preparing your workspace.",
    status: "pending",
  },
]);

const isAuthDenied = computed(
  () =>
    step.value === "migrate-form" &&
    (errorMessage.value.toLowerCase().includes("denied") ||
      errorMessage.value.toLowerCase().includes("authorization")),
);

const showInvalidSheetId = computed(
  () =>
    errorMessage.value && !isAuthDenied.value && step.value === "migrate-form",
);
</script>

<template>
  <div class="onboarding" data-cy="onboarding-root">
    <span class="onboarding__brand">dojo</span>

    <div class="onboarding__card">
      <!-- Screen 1: Choose path -->
      <template v-if="step === 'choose'">
        <p class="onboarding__eyebrow">FIRST RUN</p>
        <h1 class="onboarding__headline">Welcome to dojo</h1>
        <p class="onboarding__copy">
          Let's get you set up. You can start with an empty app or migrate your
          existing records from an Aspire Budgeting Google Sheet.
        </p>

        <Surface variant="raised" padding="0" :border="true">
          <Inline
            gap="var(--space-lg)"
            align="center"
            class="onboarding__choice-row"
          >
            <span
              class="onboarding__choice-icon onboarding__choice-icon--muted"
            >
              <PhFileText class="onboarding__choice-svg" :size="24" />
            </span>
            <div class="onboarding__choice-text">
              <span class="onboarding__choice-title">Start empty</span>
              <span class="onboarding__choice-desc"
                >Create a new dojo workspace with no data. You can add budgets
                and records from scratch.</span
              >
            </div>
            <Button variant="primary" @click="handleStartEmpty">
              Start empty
            </Button>
          </Inline>
        </Surface>

        <Surface variant="raised" padding="0" :border="true">
          <Inline
            gap="var(--space-lg)"
            align="center"
            class="onboarding__choice-row"
          >
            <span
              class="onboarding__choice-icon onboarding__choice-icon--accent"
            >
              <PhTable class="onboarding__choice-svg" :size="24" />
            </span>
            <div class="onboarding__choice-text">
              <span class="onboarding__choice-title">Migrate from Aspire</span>
              <span class="onboarding__choice-desc"
                >Import your budgets, actuals, and related data from a Google
                Aspire sheet.</span
              >
            </div>
            <Button variant="primary" @click="step = 'migrate-form'">
              Migrate from Aspire
            </Button>
          </Inline>
        </Surface>
      </template>

      <!-- Screen 2: Migration form -->
      <template
        v-if="step === 'migrate-form' && !showInvalidSheetId && !isAuthDenied"
      >
        <p class="onboarding__eyebrow">ASPIRE MIGRATION</p>
        <h1 class="onboarding__headline">Migrate from Aspire</h1>
        <p class="onboarding__copy">
          Dojo will request read access to the specified Google Sheet in order
          to import your budgets, actuals, and related data.
        </p>

        <TextField
          v-model="sheetId"
          label="Google Sheet ID"
          placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
          helper="Enter the Google Sheet ID only (the long string of letters and numbers in the URL)."
        />

        <Divider />

        <Inline
          gap="var(--space-sm)"
          align="center"
          class="onboarding__form-actions"
        >
          <Button variant="secondary" @click="handleCancel">Cancel</Button>
          <Button
            variant="primary"
            :disabled="!sheetId.trim()"
            @click="handleSubmitSheet"
          >
            Submit
          </Button>
        </Inline>
      </template>

      <!-- Screen 6: Invalid Sheet ID -->
      <template v-if="showInvalidSheetId">
        <Inline
          gap="var(--space-xs)"
          align="center"
          class="onboarding__back-link"
          tag="button"
          @click="handleBack"
        >
          <PhArrowLeft class="onboarding__back-icon" :size="16" />
          Back
        </Inline>

        <p class="onboarding__eyebrow onboarding__eyebrow--centered">
          STEP 2 OF 4
        </p>
        <h1 class="onboarding__headline">Migrate from Aspire</h1>
        <p class="onboarding__copy">
          Enter the Google Sheet ID from your Aspire export to import your
          budgets, actuals, and related data.
        </p>

        <TextField
          v-model="sheetId"
          label="Google Sheet ID"
          placeholder=""
          :error="'Enter a valid Google Sheet ID.'"
        />

        <Surface variant="muted" padding="var(--space-lg)" :border="true">
          <Inline gap="var(--space-sm)" align="start">
            <span class="onboarding__info-icon" aria-hidden="true">
              <PhInfo :size="20" />
            </span>
            <div class="onboarding__info-copy">
              <p class="onboarding__info-text">
                The Google Sheet ID is the long string in your Aspire export
                URL, between /d/ and /edit.
              </p>
              <a href="#" class="onboarding__info-link">
                Learn how to find your Sheet ID
                <PhArrowSquareOut class="onboarding__link-icon" :size="14" />
              </a>
            </div>
          </Inline>
        </Surface>

        <Divider />

        <Inline
          gap="var(--space-sm)"
          align="center"
          class="onboarding__form-actions"
        >
          <Button variant="secondary" @click="handleCancel">Cancel</Button>
          <Button
            variant="primary"
            :disabled="!sheetId.trim()"
            @click="handleSubmitSheet"
          >
            Submit
          </Button>
        </Inline>
      </template>

      <!-- Screen 7: Auth Denied -->
      <template v-if="isAuthDenied">
        <p class="onboarding__eyebrow">FIRST RUN</p>
        <h1 class="onboarding__headline">Migrate from Aspire</h1>
        <p class="onboarding__copy">
          Import your budgets, actuals, and related data from a Google Aspire
          sheet.
        </p>

        <Surface
          variant="muted"
          padding="var(--space-lg)"
          :border="true"
          class="onboarding__error-banner"
        >
          <Inline gap="var(--space-md)" align="start">
            <span class="onboarding__error-icon" aria-hidden="true">
              <PhWarningCircle :size="20" weight="fill" />
            </span>
            <div class="onboarding__error-copy">
              <p class="onboarding__error-title">
                Google authorization was denied
              </p>
              <p class="onboarding__error-desc">
                We couldn't access your Google Account. Please try again or
                cancel to return.
              </p>
            </div>
          </Inline>
        </Surface>

        <TextField
          v-model="sheetId"
          label="Google Sheet ID"
          placeholder="e.g. 1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"
          helper="Find this in the URL of your Aspire Google Sheet."
        />

        <Divider />

        <Inline
          gap="var(--space-sm)"
          align="center"
          class="onboarding__form-actions"
        >
          <Button variant="secondary" @click="handleCancel">Cancel</Button>
          <Button
            variant="primary"
            :disabled="!sheetId.trim()"
            @click="handleSubmitSheet"
          >
            Submit
          </Button>
        </Inline>
      </template>

      <!-- Screen 3: Progress -->
      <template v-if="step === 'progress'">
        <p class="onboarding__eyebrow">MIGRATION IN PROGRESS</p>
        <h1 class="onboarding__headline">Importing from Aspire</h1>
        <p class="onboarding__copy">
          Dojo is importing and validating your data. You can keep this window
          open — we'll notify you when it's ready.
        </p>

        <Divider />

        <ProgressBar
          :value="progressPercent"
          :show-value="true"
          :label="progressLabel"
          variant="positive"
        />

        <StatusStepList :steps="statusSteps" />
      </template>

      <!-- Screen 4: Complete -->
      <template v-if="step === 'complete'">
        <p class="onboarding__eyebrow">IMPORT COMPLETE</p>
        <h1 class="onboarding__headline">Migration complete</h1>

        <span class="onboarding__complete-icon" aria-hidden="true">
          <PhCheck :size="28" weight="bold" />
        </span>

        <p class="onboarding__copy">
          Your Aspire data was imported and validated successfully.
        </p>

        <Divider />

        <Inline
          gap="var(--space-sm)"
          align="center"
          class="onboarding__form-actions"
        >
          <Button variant="secondary" @click="showDetails = true">
            Details
          </Button>
          <Button variant="primary" @click="handleContinue">
            Continue to app
          </Button>
        </Inline>
      </template>
    </div>

    <ImportDetailsModal
      :visible="showDetails"
      :result="importResult"
      @close="showDetails = false"
    />
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

.onboarding__brand {
  position: fixed;
  top: var(--space-xl);
  left: var(--space-xl);
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
  letter-spacing: var(--text-headline-lg-letter-spacing);
  color: var(--color-primary);
}

.onboarding__card {
  width: min(100%, 560px);
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-2xl);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
}

.onboarding__eyebrow {
  margin: 0;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
  color: var(--color-primary);
  text-align: center;
}

.onboarding__eyebrow--centered {
  text-align: center;
}

.onboarding__headline {
  margin: 0;
  text-align: center;
  color: var(--color-primary);
  font-family: var(--text-display-lg-font-family);
  font-size: var(--text-display-lg-font-size);
  font-weight: var(--text-display-lg-font-weight);
  line-height: var(--text-display-lg-line-height);
  letter-spacing: var(--text-display-lg-letter-spacing);
}

.onboarding__copy {
  margin: 0;
  text-align: center;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-lg-font-family);
  font-size: var(--text-body-lg-font-size);
  font-weight: var(--text-body-lg-font-weight);
  line-height: var(--text-body-lg-line-height);
}

.onboarding__choice-row {
  padding: var(--space-lg);
}

.onboarding__choice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.onboarding__choice-icon--muted {
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
}

.onboarding__choice-icon--accent {
  background: color-mix(in srgb, var(--color-accent) 18%, var(--color-surface));
  color: var(--color-accent);
}

.onboarding__choice-svg {
  width: 24px;
  height: 24px;
}

.onboarding__choice-text {
  display: grid;
  gap: var(--space-xs);
  flex: 1;
  min-width: 0;
}

.onboarding__choice-title {
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
  color: var(--color-on-surface);
}

.onboarding__choice-desc {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}

.onboarding__form-actions {
  justify-content: flex-end;
}

.onboarding__back-link {
  display: inline-flex;
  align-self: start;
  padding: 0;
  border: 0;
  background: none;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  cursor: pointer;
}

.onboarding__back-link:hover {
  color: var(--color-primary);
}

.onboarding__back-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.onboarding__info-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--color-info);
}

.onboarding__info-icon svg {
  width: 20px;
  height: 20px;
}

.onboarding__info-copy {
  display: grid;
  gap: var(--space-sm);
}

.onboarding__info-text {
  margin: 0;
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}

.onboarding__info-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-primary);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  text-decoration: none;
}

.onboarding__info-link:hover {
  text-decoration: underline;
}

.onboarding__link-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.onboarding__error-banner {
  background: var(--color-error-container);
  border-color: var(--color-error-container);
}

.onboarding__error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--color-error);
  color: var(--color-on-primary);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: 700;
  line-height: 1;
  flex-shrink: 0;
}

.onboarding__error-copy {
  display: grid;
  gap: var(--space-xs);
}

.onboarding__error-title {
  margin: 0;
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-body-md-line-height);
  color: var(--color-error);
}

.onboarding__error-desc {
  margin: 0;
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  color: var(--color-on-surface-muted);
}

.onboarding__complete-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  margin: 0 auto;
  border-radius: var(--radius-full);
  background: var(--color-positive-container);
  color: var(--color-positive);
}

.onboarding__complete-icon svg {
  width: 28px;
  height: 28px;
}
</style>
