<script setup lang="ts">
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

withDefaults(
  defineProps<{
    items: NavigationRailItem[];
    expanded?: boolean;
    ariaLabel?: string;
    width?: string;
    fullHeight?: boolean;
    collapsible?: boolean;
    brand?: string;
  }>(),
  {
    expanded: false,
    ariaLabel: "Navigation rail",
    width: undefined,
    fullHeight: false,
    collapsible: false,
    brand: undefined,
  },
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
    transactions: [{ tag: "path", attrs: { d: "M5 7h14M12 7v10" } }],
    budget: [
      { tag: "path", attrs: { d: "M7 18h10M8 18V6h8v12" } },
      { tag: "path", attrs: { d: "M10 10h4M10 13h4" } },
    ],
    assets: [{ tag: "path", attrs: { d: "M5 15h4l2-6 3 9 2-5h3" } }],
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
</script>

<template>
  <nav
    class="navigation-rail"
    :class="{
      'navigation-rail--expanded': expanded,
      'navigation-rail--full-height': fullHeight,
    }"
    :style="width && !expanded ? { width } : undefined"
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
        <span v-if="expanded" class="navigation-rail__label">{{
          item.visibleLabel ?? item.label
        }}</span>
        <span
          v-if="item.badge !== undefined && expanded"
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
        expanded ? 'Collapse navigation rail' : 'Expand navigation rail'
      "
      @click="emit('toggle')"
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
            v-for="(part, index) in iconParts(expanded ? 'collapse' : 'expand')"
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
  width: var(--space-nav-collapsed);
  display: grid;
  gap: 0;
  padding: 0;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  overflow: hidden;
}

.navigation-rail--expanded {
  width: var(--space-nav-expanded);
}

.navigation-rail--full-height {
  height: 100%;
  grid-template-rows: 1fr auto;
}

.navigation-rail__items {
  display: grid;
  gap: var(--space-xs);
  align-content: start;
  min-width: 0;
  padding: var(--space-sm) 0;
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
  border-radius: 0;
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
  border-top: 1px solid var(--color-outline);
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
  padding: var(--space-sm) 10px;
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
  color: var(--color-primary);
  letter-spacing: -0.01em;
}

.navigation-rail:not(.navigation-rail--expanded) .navigation-rail__brand {
  text-align: center;
  padding: var(--space-sm) 0;
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
</style>
