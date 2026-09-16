<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import AssetsLiabilitiesPage from "../pages/AssetsLiabilitiesPage.vue";

const route = useRoute();
const showOverviewBehindOverlay = computed(() => route.path.endsWith("/add"));
</script>

<template>
  <AssetsLiabilitiesPage v-if="showOverviewBehindOverlay" />
  <router-view />
</template>
