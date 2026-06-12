<script setup lang="ts">
defineProps<{ modelValue: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="field">
    <span>Sheet URL or ID</span>
    <input :value="modelValue" type="text" @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)" />
  </label>
</template>
