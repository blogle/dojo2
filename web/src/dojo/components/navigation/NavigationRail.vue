<script setup lang="ts">
import { computed, ref } from "vue";

const emit = defineEmits<{
  toggle: [];
}>();

interface IconPart {
  tag: "path" | "rect" | "circle";
  attrs: Record<string, number | string>;
}

export interface NavigationRailItem {
  kind: "route" | "anchor";
  key: string;
  label: string;
  visibleLabel?: string;
  icon: string;
  href: string;
  badge?: string | number;
  current?: boolean;
  interactive?: boolean;
}

const props = withDefaults(
  defineProps<{
    items: NavigationRailItem[];
    expanded?: boolean | null;
    ariaLabel?: string;
    width?: string;
    fullHeight?: boolean;
    fixed?: boolean;
    collapsible?: boolean;
    brand?: string;
  }>(),
  {
    expanded: null,
    ariaLabel: "Navigation rail",
    width: undefined,
    fullHeight: false,
    fixed: false,
    collapsible: true,
    brand: undefined,
  },
);

const internalExpanded = ref(false);
const effectiveExpanded = computed(
  () => props.expanded ?? internalExpanded.value,
);

const iconParts = (icon: string): IconPart[] => {
  const glyphs: Record<string, IconPart[]> = {
    foundations: [
      { tag: "rect", attrs: { x: 4, y: 4, width: 6, height: 6, rx: 1 } },
      { tag: "rect", attrs: { x: 14, y: 4, width: 6, height: 6, rx: 1 } },
      { tag: "rect", attrs: { x: 4, y: 14, width: 6, height: 6, rx: 1 } },
      { tag: "rect", attrs: { x: 14, y: 14, width: 6, height: 6, rx: 1 } },
    ],
    layout: [
      { tag: "rect", attrs: { x: 4, y: 5, width: 16, height: 3, rx: 1.5 } },
      { tag: "rect", attrs: { x: 4, y: 11, width: 16, height: 3, rx: 1.5 } },
      { tag: "rect", attrs: { x: 4, y: 17, width: 16, height: 3, rx: 1.5 } },
    ],
    navigation: [
      { tag: "rect", attrs: { x: 4, y: 4, width: 4, height: 16, rx: 1 } },
      { tag: "rect", attrs: { x: 11, y: 6, width: 9, height: 2.5, rx: 1.25 } },
      { tag: "rect", attrs: { x: 11, y: 11, width: 9, height: 2.5, rx: 1.25 } },
      { tag: "rect", attrs: { x: 11, y: 16, width: 9, height: 2.5, rx: 1.25 } },
    ],
    dashboard: [
      { tag: "path", attrs: { d: "M5 18V9" } },
      { tag: "path", attrs: { d: "M10 18V6" } },
      { tag: "path", attrs: { d: "M15 18v-4" } },
      { tag: "path", attrs: { d: "M4 20h16" } },
    ],
    transactions: [
      { tag: "rect", attrs: { x: 6, y: 4, width: 12, height: 16, rx: 1.5 } },
      { tag: "path", attrs: { d: "M9 8h6M9 12h6M9 16h4" } },
    ],
    budget: [
      { tag: "circle", attrs: { cx: 12, cy: 12, r: 7 } },
      { tag: "path", attrs: { d: "M12 5v14M5 12h14" } },
      { tag: "path", attrs: { d: "M7 7l10 10M17 7L7 17" } },
    ],
    assets: [
      { tag: "circle", attrs: { cx: 12, cy: 12, r: 7 } },
      {
        tag: "path",
        attrs: { d: "M5 12h14M12 5a10 10 0 010 14M12 5a10 10 0 000 14" },
      },
    ],
    expand: [{ tag: "path", attrs: { d: "M9 6l6 6-6 6" } }],
    collapse: [{ tag: "path", attrs: { d: "M15 6l-6 6 6 6" } }],
  };

  return glyphs[icon] ?? [{ tag: "circle", attrs: { cx: 12, cy: 12, r: 4 } }];
};

const onItemClick = (event: MouseEvent, item: NavigationRailItem) => {
  if (item.interactive === false) {
    event.preventDefault();
  }
};

const toggleExpanded = () => {
  if (props.expanded === null) {
    internalExpanded.value = !internalExpanded.value;
  }
  emit("toggle");
};
</script>

<template>
  <nav
    class="navigation-rail"
    :class="{
      'navigation-rail--expanded': effectiveExpanded,
      'navigation-rail--full-height': fullHeight,
      'navigation-rail--fixed': fixed,
    }"
    :style="width && !effectiveExpanded ? { width } : undefined"
    :aria-label="ariaLabel"
    data-cy="navigation-rail-root"
  >
    <div class="navigation-rail__items">
      <span v-if="brand" class="navigation-rail__brand">{{ brand }}</span>
      <a
        v-for="item in items"
        :key="item.key"
        :href="item.href"
        class="navigation-rail__item"
        :class="{ 'navigation-rail__item--current': item.current }"
        :data-cy="`navigation-rail-item-${item.key}`"
        :aria-label="item.label"
        :aria-current="item.current ? 'page' : undefined"
        :aria-disabled="item.interactive === false ? 'true' : undefined"
        @click="onItemClick($event, item)"
      >
        <span class="navigation-rail__icon" aria-hidden="true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <component
              :is="part.tag"
              v-for="(part, index) in iconParts(item.icon)"
              :key="`${item.key}-${index}`"
              v-bind="part.attrs"
            />
          </svg>
        </span>
        <span v-if="effectiveExpanded" class="navigation-rail__label">{{
          item.visibleLabel ?? item.label
        }}</span>
        <span
          v-if="item.badge !== undefined && effectiveExpanded"
          class="navigation-rail__badge"
          >{{ item.badge }}</span
        >
      </a>
    </div>

    <button
      v-if="collapsible"
      type="button"
      class="navigation-rail__toggle"
      data-cy="navigation-rail-toggle"
      :aria-label="
        effectiveExpanded
          ? 'Collapse navigation rail'
          : 'Expand navigation rail'
      "
      @click="toggleExpanded"
    >
      <span class="navigation-rail__icon" aria-hidden="true">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <component
            :is="part.tag"
            v-for="(part, index) in iconParts(
              effectiveExpanded ? 'collapse' : 'expand',
            )"
            :key="`toggle-${index}`"
            v-bind="part.attrs"
          />
        </svg>
      </span>
    </button>
  </nav>
</template>

<style scoped>
.navigation-rail {
  box-sizing: border-box;
  width: var(--space-nav-collapsed);
  display: grid;
  gap: 0;
  padding: var(--space-sm);
  border-right: 1px solid var(--color-outline);
  background: var(--color-surface);
  overflow: hidden;
  transition: width var(--transition-normal) var(--transition-ease-out);
}

.navigation-rail--fixed:not(.navigation-rail--full-height) {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 10;
}

.navigation-rail--expanded {
  width: var(--space-nav-expanded);
}

.navigation-rail--full-height {
  position: sticky;
  top: 0;
  align-self: flex-start;
  min-height: 100vh;
  height: 100vh;
  grid-template-rows: 1fr auto;
}

.navigation-rail__items {
  display: grid;
  gap: var(--space-xs);
  align-content: start;
  min-width: 0;
  padding: 0;
}

.navigation-rail__item,
.navigation-rail__toggle {
  appearance: none;
  min-height: 40px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0 10px;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface-muted);
  text-decoration: none;
}

.navigation-rail:not(.navigation-rail--expanded) .navigation-rail__item,
.navigation-rail:not(.navigation-rail--expanded) .navigation-rail__toggle {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
}

.navigation-rail__toggle {
  width: 100%;
  cursor: pointer;
  justify-content: center;
}

.navigation-rail__item:hover,
.navigation-rail__toggle:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.navigation-rail__item--current {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.navigation-rail__brand {
  display: block;
  padding: var(--space-sm) 0 var(--space-xl);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
  color: var(--color-primary);
  letter-spacing: -0.01em;
}

.navigation-rail:not(.navigation-rail--expanded) .navigation-rail__brand {
  text-align: center;
  padding: var(--space-sm) 0 var(--space-xl);
}

.navigation-rail__icon {
  width: 20px;
  display: inline-flex;
  justify-content: center;
  flex: 0 0 20px;
}

.navigation-rail__icon :deep(svg) {
  width: 16px;
  height: 16px;
}

.navigation-rail__label {
  min-width: 0;
  flex: 1;
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.navigation-rail__badge {
  min-width: 18px;
  padding: 1px 6px;
  border-radius: var(--radius-all);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--text-caption-font-family);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
}

@media (max-width: 720px) {
  .navigation-rail--fixed:not(.navigation-rail--full-height) {
    position: static;
  }
}
</style>
