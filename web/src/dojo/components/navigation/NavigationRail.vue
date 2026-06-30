<script setup lang="ts">
export interface NavigationRailItem {
  kind: "route" | "anchor";
  key: string;
  label: string;
  icon: string;
  href: string;
  badge?: string | number;
  current?: boolean;
}

withDefaults(
  defineProps<{
    items: NavigationRailItem[];
    expanded?: boolean;
    ariaLabel?: string;
    compact?: boolean;
    width?: string;
  }>(),
  {
    expanded: false,
    ariaLabel: "Navigation rail",
    compact: false,
    width: undefined,
  },
);
</script>

<template>
  <nav
    class="navigation-rail"
    :class="{
      'navigation-rail--expanded': expanded,
      'navigation-rail--compact': compact,
    }"
    :style="width ? { width } : undefined"
    :aria-label="ariaLabel"
    data-cy="navigation-rail-root"
  >
    <a
      v-for="item in items"
      :key="item.key"
      :href="item.href"
      class="navigation-rail__item"
      :class="{ 'navigation-rail__item--current': item.current }"
      :aria-label="item.label"
      :aria-current="item.current ? 'page' : undefined"
    >
      <span class="navigation-rail__icon" aria-hidden="true">{{ item.icon }}</span>
      <span v-if="expanded" class="navigation-rail__label">{{ item.label }}</span>
      <span v-if="item.badge !== undefined" class="navigation-rail__badge">{{ item.badge }}</span>
    </a>
  </nav>
</template>

<style scoped>
.navigation-rail {
  width: var(--space-nav-collapsed);
  display: grid;
  gap: var(--space-xs);
  padding: var(--space-sm);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
}

.navigation-rail--expanded {
  width: var(--space-nav-expanded);
}

.navigation-rail--compact {
  width: var(--layout-quick-nav-width);
  padding: 0;
  gap: 6px;
  border: 0;
  background: transparent;
}

.navigation-rail__item {
  min-height: 40px;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0 10px;
  border-radius: var(--radius-all);
  color: var(--color-on-surface-muted);
  text-decoration: none;
}

.navigation-rail__item:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.navigation-rail__item--current {
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.navigation-rail--compact .navigation-rail__item {
  min-height: var(--layout-quick-nav-item-size);
  justify-content: center;
  padding: 0;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
}

.navigation-rail--compact .navigation-rail__item:hover {
  background: var(--color-surface-muted);
}

.navigation-rail__icon {
  width: 20px;
  display: inline-flex;
  justify-content: center;
  flex: 0 0 20px;
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
