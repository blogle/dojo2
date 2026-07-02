<script setup lang="ts">
type IconPart = {
  tag: "path" | "circle" | "rect";
  attrs: Record<string, string | number>;
};

const props = withDefaults(
  defineProps<{
    name?: string | null;
  }>(),
  {
    name: undefined,
  },
);

const iconParts: Record<string, IconPart[]> = {
  groceries: [
    { tag: "path", attrs: { d: "M6 7h12l-1.5 10h-9L6 7Z" } },
    { tag: "path", attrs: { d: "M9 7a3 3 0 0 1 6 0" } },
    { tag: "path", attrs: { d: "M10 11h4" } },
  ],
  home: [
    { tag: "path", attrs: { d: "M4 11.5 12 5l8 6.5" } },
    { tag: "path", attrs: { d: "M6.5 10.5V19h11v-8.5" } },
    { tag: "path", attrs: { d: "M10 19v-5h4v5" } },
  ],
  car: [
    { tag: "path", attrs: { d: "M6 15h12l-1.5-5h-9L6 15Z" } },
    { tag: "path", attrs: { d: "M5 15v3M19 15v3" } },
    { tag: "circle", attrs: { cx: 8, cy: 18, r: 1.2 } },
    { tag: "circle", attrs: { cx: 16, cy: 18, r: 1.2 } },
  ],
  utilities: [{ tag: "path", attrs: { d: "M13 3 6 14h5l-1 7 8-12h-5l1-6Z" } }],
  dining: [
    { tag: "path", attrs: { d: "M7 4v16" } },
    { tag: "path", attrs: { d: "M5 4v5a2 2 0 0 0 4 0V4" } },
    { tag: "path", attrs: { d: "M16 4v16" } },
    { tag: "path", attrs: { d: "M16 4c2 1.5 3 4 2 7h-2" } },
  ],
  medical: [
    { tag: "path", attrs: { d: "M12 5v14M5 12h14" } },
    { tag: "rect", attrs: { x: 4, y: 4, width: 16, height: 16, rx: 4 } },
  ],
  travel: [
    { tag: "path", attrs: { d: "M4 13 20 6l-5 14-3-6-8-1Z" } },
    { tag: "path", attrs: { d: "m12 14 8-8" } },
  ],
  savings: [
    { tag: "path", attrs: { d: "M5 11c0-3 3-5 7-5s7 2 7 5-3 5-7 5-7-2-7-5Z" } },
    { tag: "path", attrs: { d: "M8 15v3h8v-3" } },
    { tag: "path", attrs: { d: "M12 8v6M10 10h4" } },
  ],
  debt: [
    { tag: "rect", attrs: { x: 4, y: 6, width: 16, height: 12, rx: 2 } },
    { tag: "path", attrs: { d: "M4 10h16M8 14h4" } },
  ],
  gift: [
    { tag: "rect", attrs: { x: 5, y: 9, width: 14, height: 10, rx: 1 } },
    { tag: "path", attrs: { d: "M12 9v10M5 13h14" } },
    { tag: "path", attrs: { d: "M12 9c-3-4-6-2-4 0M12 9c3-4 6-2 4 0" } },
  ],
  pet: [
    { tag: "circle", attrs: { cx: 8, cy: 9, r: 1.5 } },
    { tag: "circle", attrs: { cx: 12, cy: 7, r: 1.5 } },
    { tag: "circle", attrs: { cx: 16, cy: 9, r: 1.5 } },
    { tag: "path", attrs: { d: "M7 16c1-4 9-4 10 0 1.2 4-11.2 4-10 0Z" } },
  ],
  education: [
    { tag: "path", attrs: { d: "M4 9 12 5l8 4-8 4-8-4Z" } },
    { tag: "path", attrs: { d: "M7 11v4c3 2 7 2 10 0v-4" } },
  ],
  entertainment: [
    { tag: "rect", attrs: { x: 4, y: 7, width: 16, height: 10, rx: 2 } },
    { tag: "path", attrs: { d: "M8 11h4M10 9v4M16 11h.01" } },
  ],
};

const parts = () =>
  iconParts[props.name ?? ""] ?? [
    { tag: "circle" as const, attrs: { cx: 12, cy: 12, r: 4 } },
  ];
</script>

<template>
  <svg
    class="icon-glyph"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    data-cy="icon-glyph-root"
  >
    <component
      :is="part.tag"
      v-for="(part, index) in parts()"
      :key="index"
      v-bind="part.attrs"
    />
  </svg>
</template>

<style scoped>
.icon-glyph {
  width: 1em;
  height: 1em;
  display: block;
}
</style>
