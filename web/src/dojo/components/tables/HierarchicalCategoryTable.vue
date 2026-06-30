<script setup lang="ts">
import { computed } from "vue";

import StateBadge from "@/dojo/components/display/StateBadge.vue";

type StateBadgeVariant =
  | "positive"
  | "warning"
  | "error"
  | "info"
  | "historical";

export interface HierarchicalCategoryColumn {
  key: string;
  label: string;
  align?: "start" | "end";
  width?: string;
}

export interface HierarchicalCategoryState {
  label: string;
  variant: StateBadgeVariant;
}

export interface HierarchicalCategoryRow {
  key: string;
  label: string;
  icon?: string;
  group?: boolean;
  expanded?: boolean;
  depth?: number;
  cells: Record<string, string>;
  cellVariants?: Record<string, "positive" | "warning" | "error">;
  states?: HierarchicalCategoryState[];
  children?: HierarchicalCategoryRow[];
}

const props = withDefaults(
  defineProps<{
    columns: HierarchicalCategoryColumn[];
    rows: HierarchicalCategoryRow[];
    expandable?: boolean;
    stickyHeader?: boolean;
    selectedKeys?: string[];
    reorderable?: boolean;
  }>(),
  {
    expandable: false,
    stickyHeader: false,
    selectedKeys: () => [],
    reorderable: false,
  },
);

const emit = defineEmits<{
  toggle: [key: string];
  select: [key: string];
}>();

const flattenRows = (rows: HierarchicalCategoryRow[]): HierarchicalCategoryRow[] => {
  const flattened: HierarchicalCategoryRow[] = [];

  const visit = (row: HierarchicalCategoryRow, depth: number) => {
    flattened.push({ ...row, depth });

    if (row.children?.length && row.expanded !== false) {
      row.children.forEach((child) => visit(child, depth + 1));
    }
  };

  rows.forEach((row) => visit(row, row.depth ?? 0));

  return flattened;
};

const visibleRows = computed(() => flattenRows(props.rows));

const isSelected = (key: string) => props.selectedKeys.includes(key);
</script>

<template>
  <div class="hierarchical-category-table" data-cy="hierarchical-category-table-root">
    <table class="hierarchical-category-table__table">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="hierarchical-category-table__head"
            :class="{
              'hierarchical-category-table__head--sticky': stickyHeader,
              'hierarchical-category-table__head--end': column.align === 'end',
            }"
            :style="column.width ? { width: column.width } : undefined"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in visibleRows"
          :key="row.key"
          class="hierarchical-category-table__row"
          :class="{
            'hierarchical-category-table__row--group': row.group,
            'hierarchical-category-table__row--selected': isSelected(row.key),
          }"
          @click="emit('select', row.key)"
        >
          <td class="hierarchical-category-table__cell">
            <div
              class="hierarchical-category-table__label-cell"
              :style="{ '--depth': String(row.depth ?? 0) }"
            >
              <button
                v-if="expandable && row.children?.length"
                type="button"
                class="hierarchical-category-table__disclosure"
                :aria-label="row.expanded === false ? 'Expand row' : 'Collapse row'"
                @click.stop="emit('toggle', row.key)"
              >
                {{ row.expanded === false ? '+' : '-' }}
              </button>
              <span
                v-else
                class="hierarchical-category-table__disclosure hierarchical-category-table__disclosure--spacer"
              />
              <span
                v-if="reorderable"
                class="hierarchical-category-table__drag-handle"
                aria-hidden="true"
              >
                ::
              </span>
              <span
                v-if="row.icon"
                class="hierarchical-category-table__row-icon"
                aria-hidden="true"
              >
                {{ row.icon }}
              </span>
              <span class="hierarchical-category-table__label">{{ row.label }}</span>
              <div v-if="row.states?.length" class="hierarchical-category-table__states">
                <StateBadge
                  v-for="state in row.states"
                  :key="`${row.key}-${state.label}`"
                  :variant="state.variant"
                  size="sm"
                >
                  {{ state.label }}
                </StateBadge>
              </div>
            </div>
          </td>
          <td
            v-for="column in columns.slice(1)"
            :key="`${row.key}-${column.key}`"
            class="hierarchical-category-table__cell"
            :class="{
              'hierarchical-category-table__cell--end': column.align === 'end',
              'hierarchical-category-table__cell--positive': row.cellVariants?.[column.key] === 'positive',
              'hierarchical-category-table__cell--warning': row.cellVariants?.[column.key] === 'warning',
              'hierarchical-category-table__cell--error': row.cellVariants?.[column.key] === 'error',
            }"
          >
            {{ row.cells[column.key] }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.hierarchical-category-table {
  width: 100%;
  overflow-x: auto;
}

.hierarchical-category-table__table {
  width: 100%;
  border-collapse: collapse;
}

.hierarchical-category-table__head {
  height: 34px;
  padding: 0 12px;
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
  text-align: left;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
}

.hierarchical-category-table__head--sticky {
  position: sticky;
  top: 0;
}

.hierarchical-category-table__head--end,
.hierarchical-category-table__cell--end {
  text-align: right;
}

.hierarchical-category-table__row {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  cursor: pointer;
}

.hierarchical-category-table__row:hover,
.hierarchical-category-table__row--selected {
  background: var(--color-surface-selected);
}

.hierarchical-category-table__row--group {
  font-weight: 600;
}

.hierarchical-category-table__cell {
  height: 42px;
  padding: 0 12px;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  vertical-align: middle;
}

.hierarchical-category-table__label-cell {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding-left: calc(var(--depth) * 16px);
}

.hierarchical-category-table__disclosure {
  min-width: 18px;
  border: 0;
  background: transparent;
  color: var(--color-on-surface-muted);
  cursor: pointer;
}

.hierarchical-category-table__disclosure--spacer {
  display: inline-block;
}

.hierarchical-category-table__drag-handle {
  color: var(--color-on-surface-muted);
  cursor: grab;
}

.hierarchical-category-table__label {
  white-space: nowrap;
}

.hierarchical-category-table__states {
  display: inline-flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-left: var(--space-xs);
}

.hierarchical-category-table__row-icon {
  color: var(--color-on-surface-muted);
  font-size: var(--text-body-sm-font-size);
}

.hierarchical-category-table__cell--positive {
  color: var(--color-positive);
}

.hierarchical-category-table__cell--warning {
  color: var(--color-warning);
}

.hierarchical-category-table__cell--error {
  color: var(--color-error);
}
</style>
