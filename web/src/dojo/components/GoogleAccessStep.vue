<script setup lang="ts">
defineProps<{
  loading: boolean;
  configured: boolean;
  fixtureMode: boolean;
  authorized: boolean;
}>();
const emit = defineEmits<{ begin: [] }>();
</script>

<template>
  <div class="step">
    <h3>Google access</h3>
    <p v-if="configured && authorized">
      Google Sheets access is active for this browser session. Paste the copied
      sheet URL or ID to import.
    </p>
    <p v-else-if="configured">
      Grant read-only Google Sheets access, then paste the copied sheet URL or
      ID.
    </p>
    <p v-else-if="fixtureMode">
      Google OAuth is not configured here. Use the fixture import path for local
      dogfooding.
    </p>
    <p v-else>Google OAuth is not configured in this environment.</p>
    <button type="button" :disabled="loading" @click="emit('begin')">
      {{
        configured
          ? authorized
            ? "Refresh OAuth"
            : "Begin OAuth"
          : "Check configuration"
      }}
    </button>
  </div>
</template>
