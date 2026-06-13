<script setup lang="ts">
defineProps<{ loading: boolean }>();
const emit = defineEmits<{ confirm: [] }>();
</script>

<template>
  <button type="button" :disabled="loading" @click="emit('confirm')">
    Import now
  </button>
</template>
