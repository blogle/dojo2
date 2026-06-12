<script setup lang="ts">
defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <label class="toggle">
    <input :checked="modelValue" type="checkbox" @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)" />
    <span>Show hidden</span>
  </label>
</template>

<style scoped>
.toggle {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.9rem;
}
</style>
