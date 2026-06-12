<script setup lang="ts">
defineProps<{ modelValue: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="field">
    <span>Month</span>
    <input :value="modelValue" type="month" @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)" />
  </label>
</template>

<style scoped>
.field {
  display: grid;
  gap: 0.25rem;
}
</style>
