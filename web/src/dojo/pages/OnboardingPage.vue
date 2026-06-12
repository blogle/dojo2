<script setup lang="ts">
import OnboardingScreen from "../components/OnboardingScreen.vue";
import { useAppState } from "../state/app";

const app = useAppState();
</script>

<template>
  <OnboardingScreen
    :import-result="app.state.importResult"
    :loading="app.state.loading || app.state.saving"
    :onboarding-info="app.state.onboardingInfo"
    @begin-google="app.beginGoogleOnboarding()"
    @import-sheet="app.importSheet($event)"
  />
</template>
