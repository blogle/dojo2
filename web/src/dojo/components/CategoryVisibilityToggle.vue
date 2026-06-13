<script setup lang="ts">
defineProps<{ hidden: boolean }>();
const emit = defineEmits<{ toggle: [value: boolean] }>();
</script>

<template>
  <button type="button" @click="emit('toggle', !hidden)">
    {{ hidden ? "Show" : "Hide" }}
  </button>
</template>
