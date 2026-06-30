<script setup lang="ts">
export interface TableColumn {
  key: string;
  label: string;
  align?: "start" | "end";
  width?: string;
}

withDefaults(
  defineProps<{
    columns: TableColumn[];
    rows: object[];
    rowKey?: string;
    stickyHeader?: boolean;
    emptyText?: string;
  }>(),
  {
    rowKey: "key",
    stickyHeader: false,
    emptyText: "No rows to display.",
  },
);
</script>

<template>
  <div class="table-shell" data-cy="table-shell-root">
    <table class="table-shell__table">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="table-shell__head"
            :class="{
              'table-shell__head--sticky': stickyHeader,
              'table-shell__head--end': column.align === 'end',
            }"
            :style="column.width ? { width: column.width } : undefined"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="rows.length === 0">
          <td class="table-shell__empty" :colspan="columns.length">
            {{ emptyText }}
          </td>
        </tr>
        <tr
          v-for="row in rows"
          :key="String((row as Record<string, unknown>)[rowKey] ?? '')"
          class="table-shell__row"
        >
          <slot name="row" :row="row" :columns="columns">
            <td
              v-for="column in columns"
              :key="column.key"
              class="table-shell__cell"
              :class="{ 'table-shell__cell--end': column.align === 'end' }"
            >
              {{ (row as Record<string, unknown>)[column.key] }}
            </td>
          </slot>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-shell {
  width: 100%;
  overflow-x: auto;
}

.table-shell__table {
  width: 100%;
  border-collapse: collapse;
}

.table-shell__head {
  padding: 0 12px;
  height: 34px;
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
  text-align: left;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
}

.table-shell__head--sticky {
  position: sticky;
  top: 0;
}

.table-shell__head--end,
.table-shell__cell--end {
  text-align: right;
}

.table-shell__row {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
}

.table-shell__cell,
.table-shell__empty {
  height: var(--space-row-height-default, 42px);
  padding: 0 12px;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  vertical-align: middle;
}

.table-shell__row:hover {
  background: var(--color-surface-selected);
}

.table-shell__empty {
  padding: var(--space-lg) 12px;
  color: var(--color-on-surface-muted);
}
</style>
