<script setup lang="ts">
import { computed, ref } from "vue";

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
  reorder: [key: string, targetKey: string, position: "before" | "after"];
}>();

const expandedState = ref<Record<string, boolean>>({});

const initExpanded = () => {
  const state: Record<string, boolean> = {};
  const walk = (rows: HierarchicalCategoryRow[]) => {
    for (const row of rows) {
      state[row.key] = row.expanded !== false;
      if (row.children?.length) walk(row.children);
    }
  };
  walk(props.rows);
  expandedState.value = state;
};

initExpanded();

const flattenRows = (rows: HierarchicalCategoryRow[]): HierarchicalCategoryRow[] => {
  const flattened: HierarchicalCategoryRow[] = [];

  const visit = (row: HierarchicalCategoryRow, depth: number) => {
    const expanded = expandedState.value[row.key] ?? true;
    flattened.push({ ...row, depth, expanded });

    if (row.children?.length && expanded) {
      row.children.forEach((child) => visit(child, depth + 1));
    }
  };

  rows.forEach((row) => visit(row, row.depth ?? 0));

  return flattened;
};

const visibleRows = computed(() => flattenRows(props.rows));

const handleToggle = (key: string) => {
  expandedState.value[key] = !expandedState.value[key];
  emit("toggle", key);
};

const isSelected = (key: string) => props.selectedKeys.includes(key);

const dragKey = ref<string | null>(null);
const dropTarget = ref<string | null>(null);
const dropPosition = ref<"before" | "after">("after");

const onDragStart = (key: string, event: DragEvent) => {
  dragKey.value = key;
  event.dataTransfer!.effectAllowed = "move";
};

const onDragOver = (key: string, event: DragEvent) => {
  event.preventDefault();
  event.dataTransfer!.dropEffect = "move";

  const target = event.currentTarget as HTMLElement;
  const rect = target.getBoundingClientRect();
  const midY = rect.top + rect.height / 2;

  dropPosition.value = event.clientY < midY ? "before" : "after";
  dropTarget.value = key;
};

const onDragEnter = (key: string, event: DragEvent) => {
  event.preventDefault();
  dropTarget.value = key;
};

const onDragLeave = () => {
  dropTarget.value = null;
};

const onDrop = (key: string) => {
  if (dragKey.value && dragKey.value !== key) {
    emit("reorder", dragKey.value, key, dropPosition.value);
  }
  dragKey.value = null;
  dropTarget.value = null;
};

const onDragEnd = () => {
  dragKey.value = null;
  dropTarget.value = null;
};

const isDragTarget = (key: string) => dropTarget.value === key;
const isDragging = (key: string) => dragKey.value === key;
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
            'hierarchical-category-table__row--drag-target': isDragTarget(row.key),
            'hierarchical-category-table__row--dragging': isDragging(row.key),
          }"
          :draggable="reorderable"
          @click="emit('select', row.key)"
          @dragstart="onDragStart(row.key, $event)"
          @dragover="onDragOver(row.key, $event)"
          @dragenter="onDragEnter(row.key, $event)"
          @dragleave="onDragLeave()"
          @drop="onDrop(row.key)"
          @dragend="onDragEnd()"
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
                :aria-label="expandedState[row.key] === false ? 'Expand row' : 'Collapse row'"
                @click.stop="handleToggle(row.key)"
              >
                <svg
                  class="hierarchical-category-table__chevron"
                  :class="{ 'hierarchical-category-table__chevron--collapsed': expandedState[row.key] === false }"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
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
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="9" cy="5" r="1.5" />
                  <circle cx="15" cy="5" r="1.5" />
                  <circle cx="9" cy="12" r="1.5" />
                  <circle cx="15" cy="12" r="1.5" />
                  <circle cx="9" cy="19" r="1.5" />
                  <circle cx="15" cy="19" r="1.5" />
                </svg>
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
  transition: background var(--transition-fast) var(--transition-ease-out);
}

.hierarchical-category-table__row:hover,
.hierarchical-category-table__row--selected {
  background: var(--color-surface-selected);
}

.hierarchical-category-table__row--group {
  font-weight: 600;
}

.hierarchical-category-table__row--dragging {
  opacity: 0.4;
}

.hierarchical-category-table__row--drag-target {
  box-shadow: inset 0 -2px 0 var(--color-positive);
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  min-height: 18px;
  border: 0;
  background: transparent;
  color: var(--color-on-surface-muted);
  cursor: pointer;
  padding: 0;
}

.hierarchical-category-table__disclosure:hover {
  color: var(--color-on-surface);
}

.hierarchical-category-table__disclosure--spacer {
  display: inline-block;
}

.hierarchical-category-table__chevron {
  width: 16px;
  height: 16px;
  transition: transform var(--transition-fast) var(--transition-ease-out);
}

.hierarchical-category-table__chevron--collapsed {
  transform: rotate(-90deg);
}

.hierarchical-category-table__drag-handle {
  display: inline-flex;
  align-items: center;
  color: var(--color-on-surface-muted);
  cursor: grab;
}

.hierarchical-category-table__drag-handle:active {
  cursor: grabbing;
}

.hierarchical-category-table__drag-handle svg {
  width: 16px;
  height: 16px;
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
