<script setup lang="ts">
defineProps<{ sortOrder: number }>();
const emit = defineEmits<{ update: [value: number] }>();
</script>

<template>
  <div class="reorder-control">
    <button type="button" @click="emit('update', sortOrder - 10)">-</button>
    <span>{{ sortOrder }}</span>
    <button type="button" @click="emit('update', sortOrder + 10)">+</button>
  </div>
</template>

<style scoped>
.reorder-control {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
}
</style>
