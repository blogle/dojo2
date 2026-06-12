<script setup lang="ts" generic="T extends { [key: string]: unknown }">
import { computed, ref } from "vue";

const props = withDefaults(
  defineProps<{
    items: T[];
    rowHeight?: number;
    viewportHeight?: number;
    overscan?: number;
  }>(),
  {
    rowHeight: 48,
    viewportHeight: 420,
    overscan: 6,
  },
);

const scrollTop = ref(0);

const startIndex = computed(() => Math.max(0, Math.floor(scrollTop.value / props.rowHeight) - props.overscan));
const visibleCount = computed(() => Math.ceil(props.viewportHeight / props.rowHeight) + props.overscan * 2);
const endIndex = computed(() => Math.min(props.items.length, startIndex.value + visibleCount.value));
const visibleItems = computed(() => props.items.slice(startIndex.value, endIndex.value));
const topPadding = computed(() => startIndex.value * props.rowHeight);
const bottomPadding = computed(() => Math.max(0, (props.items.length - endIndex.value) * props.rowHeight));

function handleScroll(event: Event): void {
  scrollTop.value = (event.target as HTMLElement).scrollTop;
}
</script>

<template>
  <div class="virtual-table" :style="{ height: `${viewportHeight}px` }" @scroll="handleScroll">
    <div :style="{ height: `${topPadding}px` }" />
    <slot :items="visibleItems" :start-index="startIndex" />
    <div :style="{ height: `${bottomPadding}px` }" />
  </div>
</template>

<style scoped>
.virtual-table {
  overflow: auto;
  border: 1px solid var(--dojo-border-brown);
  background: var(--dojo-bg-off-white);
}
</style>
