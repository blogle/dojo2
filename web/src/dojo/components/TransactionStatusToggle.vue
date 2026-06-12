<script setup lang="ts">
defineProps<{ status: "PENDING" | "CLEARED" }>();
const emit = defineEmits<{ toggle: [] }>();
</script>

<template>
  <button class="status-toggle" type="button" @click="emit('toggle')">
    {{ status === "PENDING" ? "Pending" : "Cleared" }}
  </button>
</template>

<style scoped>
.status-toggle {
  border: 1px solid var(--dojo-border-brown);
  background: transparent;
  padding: 0.3rem 0.6rem;
}
</style>
