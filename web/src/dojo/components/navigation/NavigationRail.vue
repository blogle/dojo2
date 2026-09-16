<script setup lang="ts">
import { computed, ref } from "vue";
import { PhCaretLeft, PhCaretRight } from "@phosphor-icons/vue";

import {
  readNavigationExpanded,
  writeNavigationExpanded,
} from "../../state/navigation";

const emit = defineEmits<{
  toggle: [expanded: boolean];
  action: [key: string];
}>();

interface IconPart {
  tag: "path" | "rect" | "circle";
  attrs: Record<string, number | string>;
}

export interface NavigationRailItem {
  kind: "route" | "anchor" | "action";
  key: string;
  label: string;
  visibleLabel?: string;
  icon: string;
  href?: string;
  badge?: string | number;
  current?: boolean;
  interactive?: boolean;
}

const props = withDefaults(
  defineProps<{
    primaryItems: NavigationRailItem[];
    secondaryItems?: NavigationRailItem[];
    expanded?: boolean | null;
    ariaLabel?: string;
    collapsible?: boolean;
    brand?: string;
  }>(),
  {
    secondaryItems: () => [],
    expanded: null,
    ariaLabel: "Navigation rail",
    collapsible: true,
    brand: undefined,
  },
);

const internalExpanded = ref(readNavigationExpanded());
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
    account: [
      { tag: "circle", attrs: { cx: 12, cy: 8, r: 3 } },
      { tag: "path", attrs: { d: "M5 20a7 7 0 0114 0" } },
    ],
  };

  return glyphs[icon] ?? [{ tag: "circle", attrs: { cx: 12, cy: 12, r: 4 } }];
};

const onItemClick = (event: MouseEvent, item: NavigationRailItem) => {
  if (item.interactive === false) {
    event.preventDefault();
    return;
  }
  if (item.kind === "action") emit("action", item.key);
};

const toggleExpanded = () => {
  const nextExpanded = !effectiveExpanded.value;
  if (props.expanded === null) {
    internalExpanded.value = nextExpanded;
  }
  writeNavigationExpanded(nextExpanded);
  emit("toggle", nextExpanded);
};
</script>

<template>
  <nav
    class="navigation-rail"
    :class="{ 'navigation-rail--expanded': effectiveExpanded }"
    :aria-label="ariaLabel"
    data-cy="navigation-rail-root"
  >
    <div class="navigation-rail__items">
      <span v-if="brand" class="navigation-rail__brand">{{ brand }}</span>
      <div class="navigation-rail__primary" aria-label="Primary destinations">
        <a
          v-for="item in primaryItems"
          :key="item.key"
          :href="item.href"
          class="navigation-rail__item"
          :class="{ 'navigation-rail__item--current': item.current }"
          :data-cy="`navigation-rail-item-${item.key}`"
          :title="!effectiveExpanded ? item.label : undefined"
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
    </div>

    <div class="navigation-rail__lower" aria-label="Navigation utilities">
      <template v-for="item in secondaryItems" :key="item.key">
        <button
          v-if="item.kind === 'action'"
          type="button"
          class="navigation-rail__item navigation-rail__action"
          :data-cy="`navigation-rail-item-${item.key}`"
          :title="!effectiveExpanded ? item.label : undefined"
          :aria-label="item.label"
          :aria-disabled="item.interactive === false ? 'true' : undefined"
          :disabled="item.interactive === false"
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
        </button>
        <a
          v-else
          :href="item.href"
          class="navigation-rail__item"
          :class="{ 'navigation-rail__item--current': item.current }"
          :data-cy="`navigation-rail-item-${item.key}`"
          :title="!effectiveExpanded ? item.label : undefined"
          :aria-label="item.label"
          :aria-current="item.current ? 'page' : undefined"
          @click="onItemClick($event, item)"
        >
          <span class="navigation-rail__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
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
        </a>
      </template>

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
        <PhCaretLeft
          v-if="effectiveExpanded"
          :size="20"
          weight="regular"
          aria-hidden="true"
        />
        <PhCaretRight v-else :size="20" weight="regular" aria-hidden="true" />
      </button>
    </div>
  </nav>
</template>

<style scoped>
.navigation-rail {
  box-sizing: border-box;
  width: var(--space-nav-collapsed);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: var(--space-sm);
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  border-right: 1px solid var(--color-outline);
  background: var(--color-surface);
  overflow: hidden;
  transition: width var(--transition-normal) var(--transition-ease-out);
}

.navigation-rail--expanded {
  width: var(--space-nav-expanded);
}

.navigation-rail__items,
.navigation-rail__lower,
.navigation-rail__primary {
  display: grid;
  gap: var(--space-xs);
  min-width: 0;
  width: 100%;
}

.navigation-rail__items {
  align-content: start;
}

.navigation-rail__lower {
  margin-top: auto;
}

.navigation-rail__item,
.navigation-rail__toggle {
  appearance: none;
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
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

.navigation-rail__action:disabled {
  cursor: default;
  opacity: 1;
}

.navigation-rail__toggle {
  width: 100%;
  cursor: pointer;
}

.navigation-rail__item:hover,
.navigation-rail__toggle:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.navigation-rail__item--current {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
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
  white-space: nowrap;
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
