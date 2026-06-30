<script setup lang="ts">
import DesignSystemPage from "./pages/DesignSystemPage.vue";
import FrontendResetPage from "./pages/FrontendResetPage.vue";

const isDesignSystemPage =
  import.meta.env.DEV && window.location.pathname === "/dev/design-system";
</script>

<template>
  <DesignSystemPage v-if="isDesignSystemPage" />
  <FrontendResetPage v-else />
</template>
