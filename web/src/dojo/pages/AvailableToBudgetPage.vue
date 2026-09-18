<script setup lang="ts">
import { computed, ref } from "vue";
import { useInfiniteQuery, useQuery } from "@tanstack/vue-query";
import { useRoute, useRouter } from "vue-router";
import { useVirtualizer, type VirtualItem } from "@tanstack/vue-virtual";

import {
  fetchAvailableToBudgetBreakdown,
  fetchAvailableToBudgetComponent,
  fetchAvailableToBudgetRecords,
} from "../api/client";
import Button from "../components/actions/Button.vue";
import CalculationFooter from "../components/data/CalculationFooter.vue";
import PageHeader from "../components/data/PageHeader.vue";
import type { AvailableToBudgetRecord } from "../types";
import { formatCurrency, formatMonth } from "../utils/currency";

const route = useRoute();
const router = useRouter();
const PAGE_SIZE = 50;
const currentMonth = new Date().toISOString().slice(0, 7);
const month = computed(() =>
  typeof route.query.month === "string" &&
  /^\d{4}-(0[1-9]|1[0-2])$/.test(route.query.month)
    ? route.query.month
    : currentMonth,
);
const selectedComponentKey = ref<string | null>(null);
const selectedGroupKey = ref<string | null>(null);
const scrollElement = ref<HTMLElement | null>(null);

const summaryQuery = useQuery({
  queryKey: computed(() => ["available-to-budget", "summary", month.value]),
  queryFn: () => fetchAvailableToBudgetBreakdown(month.value),
});

const componentQuery = useQuery({
  queryKey: computed(() => [
    "available-to-budget",
    "component",
    month.value,
    selectedComponentKey.value,
  ]),
  queryFn: () =>
    fetchAvailableToBudgetComponent(selectedComponentKey.value!, month.value),
  enabled: computed(() => selectedComponentKey.value !== null),
});

const recordsQuery = useInfiniteQuery({
  queryKey: computed(() => [
    "available-to-budget",
    "records",
    month.value,
    selectedComponentKey.value,
    selectedGroupKey.value,
  ]),
  queryFn: ({ pageParam }) =>
    fetchAvailableToBudgetRecords(
      selectedComponentKey.value!,
      month.value,
      selectedGroupKey.value!,
      pageParam,
      PAGE_SIZE,
    ),
  initialPageParam: 0,
  getNextPageParam: (lastPage) =>
    lastPage.has_more ? lastPage.offset + lastPage.limit : undefined,
  enabled: computed(
    () =>
      selectedComponentKey.value !== null && selectedGroupKey.value !== null,
  ),
});

const records = computed(
  () => recordsQuery.data.value?.pages.flatMap((page) => page.items) ?? [],
);
const component = computed(() => componentQuery.data.value?.component ?? null);
const group = computed(
  () =>
    componentQuery.data.value?.groups.find(
      (item) => item.key === selectedGroupKey.value,
    ) ?? null,
);
const showCategory = computed(
  () =>
    selectedComponentKey.value !== "allocations" &&
    selectedComponentKey.value !== "transfers",
);
const total = computed(
  () => summaryQuery.data.value?.available_to_budget_minor ?? null,
);
const recordsTotal = computed(
  () => recordsQuery.data.value?.pages[0]?.total ?? 0,
);
const asOfDate = computed(() => summaryQuery.data.value?.as_of_date ?? null);

const rowVirtualizer = useVirtualizer(
  computed(() => ({
    count: records.value.length,
    getScrollElement: () => scrollElement.value,
    estimateSize: () => 52,
    overscan: 8,
    getItemKey: (index: number) =>
      records.value[index]?.id ?? `record-${index}`,
  })),
);
const virtualRows = computed(() => rowVirtualizer.value.getVirtualItems());
const totalRowsHeight = computed(() => rowVirtualizer.value.getTotalSize());
const virtualRecords = computed<
  { virtualRow: VirtualItem; record: AvailableToBudgetRecord }[]
>(() =>
  virtualRows.value.flatMap((virtualRow) => {
    const record = records.value[virtualRow.index];
    return record ? [{ virtualRow, record }] : [];
  }),
);

function signedAmount(value: number): string {
  return `${value > 0 ? "+" : ""}${formatCurrency(value)}`;
}

function directionLabel(
  direction: "increases" | "decreases" | "neutral",
): string {
  if (direction === "increases") return "increases Available to budget";
  if (direction === "decreases") return "decreases Available to budget";
  return "no net change";
}

function constituentNoun(componentKey: string | null, plural = true): string {
  if (componentKey === "allocations") return plural ? "categories" : "category";
  if (componentKey === "transfers") {
    return plural ? "transfer paths" : "transfer path";
  }
  return plural ? "accounts" : "account";
}

function sourceEntryLabel(count: number): string {
  return `${count} source ${count === 1 ? "entry" : "entries"}`;
}

function formatDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function errorMessage(error: unknown): string | null {
  return error instanceof Error
    ? error.message
    : error
      ? "The request failed."
      : null;
}

function selectComponent(key: string): void {
  selectedComponentKey.value = key;
  selectedGroupKey.value = null;
}

function selectGroup(key: string): void {
  selectedGroupKey.value = key;
}

function zoomToComponents(): void {
  selectedComponentKey.value = null;
  selectedGroupKey.value = null;
}

function zoomToComponent(): void {
  selectedGroupKey.value = null;
}

function backToBudget(): void {
  router.push({ path: "/budgets", query: { month: month.value } });
}

function handleScroll(): void {
  const element = scrollElement.value;
  if (
    !element ||
    !recordsQuery.hasNextPage.value ||
    recordsQuery.isFetchingNextPage.value
  )
    return;
  if (element.scrollHeight - element.scrollTop - element.clientHeight < 240) {
    recordsQuery.fetchNextPage();
  }
}
</script>

<template>
  <div class="available-to-budget-page" data-cy="available-to-budget-page-root">
    <main class="available-to-budget-page__main">
      <PageHeader
        title="Available to budget"
        subtitle="Current-state calculation"
      >
        <template #eyebrow>
          <nav
            class="available-to-budget-page__breadcrumb"
            aria-label="Available to budget path"
          >
            <button type="button" @click="backToBudget">Budget</button>
            <span aria-hidden="true">/</span>
            <span v-if="!selectedComponentKey" aria-current="page"
              >Available to budget</span
            >
            <button v-else type="button" @click="zoomToComponents">
              Available to budget
            </button>
            <template v-if="component">
              <span aria-hidden="true">/</span>
              <span v-if="!selectedGroupKey" aria-current="page">{{
                component.label
              }}</span>
              <button v-else type="button" @click="zoomToComponent">
                {{ component.label }}
              </button>
            </template>
            <template v-if="group && selectedGroupKey">
              <span aria-hidden="true">/</span>
              <span aria-current="page">{{ group.label }}</span>
            </template>
          </nav>
        </template>
        <template #actions>
          <Button variant="secondary" @click="backToBudget"
            >Back to Budget</Button
          >
        </template>
      </PageHeader>

      <section
        class="available-to-budget-page__context"
        aria-label="Calculation context"
      >
        <div>
          <span class="available-to-budget-page__label"
            >Available to budget</span
          >
          <strong class="available-to-budget-page__total">
            {{ total === null ? "—" : formatCurrency(total) }}
          </strong>
        </div>
        <div>
          <span class="available-to-budget-page__label">Budget context</span
          ><span>{{ formatMonth(month) }}</span>
        </div>
        <div>
          <span class="available-to-budget-page__label">As of</span
          ><span>{{ asOfDate ? formatDate(asOfDate) : "—" }}</span>
        </div>
        <div>
          <span class="available-to-budget-page__label">Calculation scope</span
          ><span>Current state</span>
        </div>
      </section>

      <section
        v-if="summaryQuery.isPending.value"
        class="available-to-budget-page__state"
      >
        Loading explanation...
      </section>
      <section
        v-else-if="errorMessage(summaryQuery.error.value)"
        class="available-to-budget-page__state available-to-budget-page__state--error"
        role="alert"
        data-cy="available-to-budget-summary-error"
      >
        <p>We could not load the Available to budget explanation.</p>
        <p>{{ errorMessage(summaryQuery.error.value) }}</p>
        <Button variant="secondary" @click="summaryQuery.refetch()"
          >Retry</Button
        >
      </section>
      <template v-else-if="summaryQuery.data.value">
        <section
          v-if="!selectedComponentKey"
          class="available-to-budget-page__surface"
          data-cy="available-to-budget-level-1"
        >
          <div class="available-to-budget-page__section-heading">
            <div>
              <h2>Calculation components</h2>
              <p>
                The Budget month is context only; this total reflects the
                current state.
              </p>
            </div>
          </div>
          <div class="available-to-budget-page__rows">
            <button
              v-for="item in summaryQuery.data.value.components"
              :key="item.key"
              class="available-to-budget-page__row"
              :class="{
                'available-to-budget-page__row--quiet': item.amount_minor === 0,
              }"
              type="button"
              :data-cy="`atb-component-${item.key}`"
              @click="selectComponent(item.key)"
            >
              <span
                ><strong>{{ item.label }}</strong
                ><small
                  >{{ directionLabel(item.direction) }} ·
                  {{ item.group_count }}
                  {{ constituentNoun(item.key) }} ·
                  {{ sourceEntryLabel(item.contribution_count) }}</small
                ></span
              >
              <strong class="available-to-budget-page__amount">{{
                signedAmount(item.amount_minor)
              }}</strong>
            </button>
          </div>
          <p
            v-if="
              total === 0 &&
              summaryQuery.data.value.components.every(
                (item) => item.contribution_count === 0,
              )
            "
            class="available-to-budget-page__empty"
            data-cy="available-to-budget-empty"
          >
            No money is currently unassigned to categories, and no source
            entries contribute to this total.
          </p>
          <CalculationFooter
            label="Available to budget"
            :value="total === null ? '—' : formatCurrency(total)"
          />
        </section>

        <section
          v-else-if="selectedComponentKey && !selectedGroupKey"
          class="available-to-budget-page__surface"
          data-cy="available-to-budget-level-2"
        >
          <div class="available-to-budget-page__section-heading">
            <div>
              <h2>{{ constituentNoun(selectedComponentKey) }}</h2>
              <p>Largest contributors first</p>
            </div>
            <Button variant="tertiary" size="sm" @click="zoomToComponents"
              >Back to components</Button
            >
          </div>
          <div
            v-if="componentQuery.isPending.value"
            class="available-to-budget-page__state"
          >
            Loading contributors...
          </div>
          <div
            v-else-if="errorMessage(componentQuery.error.value)"
            class="available-to-budget-page__state available-to-budget-page__state--error"
            role="alert"
            data-cy="available-to-budget-component-error"
          >
            <p>{{ errorMessage(componentQuery.error.value) }}</p>
            <Button variant="secondary" @click="componentQuery.refetch()"
              >Retry</Button
            >
          </div>
          <template v-else-if="componentQuery.data.value">
            <div
              v-if="componentQuery.data.value.groups.length > 0"
              class="available-to-budget-page__rows"
            >
              <button
                v-for="item in componentQuery.data.value.groups"
                :key="item.key"
                class="available-to-budget-page__row"
                type="button"
                :data-cy="`atb-group-${item.key}`"
                @click="selectGroup(item.key)"
              >
                <span
                  ><strong>{{ item.label }}</strong
                  ><small
                    >{{ directionLabel(item.direction) }} ·
                    {{ sourceEntryLabel(item.record_count) }}</small
                  ></span
                ><strong class="available-to-budget-page__amount">{{
                  signedAmount(item.amount_minor)
                }}</strong>
              </button>
            </div>
            <p
              v-else
              class="available-to-budget-page__empty"
              data-cy="available-to-budget-component-empty"
            >
              No source entries contribute to this component.
            </p>
          </template>
          <CalculationFooter
            label="Component total"
            :value="component ? formatCurrency(component.amount_minor) : '—'"
          />
        </section>

        <section
          v-else-if="selectedGroupKey"
          class="available-to-budget-page__surface"
          data-cy="available-to-budget-level-3"
        >
          <div class="available-to-budget-page__section-heading">
            <div>
              <h2>Source entries</h2>
              <p>{{ sourceEntryLabel(group?.record_count ?? 0) }}</p>
            </div>
            <Button variant="tertiary" size="sm" @click="zoomToComponent"
              >Back to {{ constituentNoun(selectedComponentKey) }}</Button
            >
          </div>
          <div
            v-if="recordsQuery.isPending.value"
            class="available-to-budget-page__state"
          >
            Loading source entries...
          </div>
          <div
            v-else-if="errorMessage(recordsQuery.error.value)"
            class="available-to-budget-page__state available-to-budget-page__state--error"
            role="alert"
            data-cy="available-to-budget-records-error"
          >
            <p>{{ errorMessage(recordsQuery.error.value) }}</p>
            <Button variant="secondary" @click="recordsQuery.refetch()"
              >Retry</Button
            >
          </div>
          <template v-else>
            <div
              ref="scrollElement"
              class="available-to-budget-page__ledger"
              @scroll="handleScroll"
            >
              <table
                :class="{
                  'available-to-budget-page__ledger--without-category':
                    !showCategory,
                }"
              >
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Entry</th>
                    <th v-if="showCategory">Category</th>
                    <th>Memo</th>
                    <th class="available-to-budget-page__number">
                      Contribution
                    </th>
                  </tr>
                </thead>
                <tbody :style="{ height: `${totalRowsHeight}px` }">
                  <tr
                    v-for="{ virtualRow, record } in virtualRecords"
                    :key="record.id"
                    :style="{ transform: `translateY(${virtualRow.start}px)` }"
                    data-cy="atb-record-row"
                  >
                    <td>{{ formatDate(record.date) }}</td>
                    <td>
                      {{ record.source_label }}
                      <span
                        v-if="record.provenance_label"
                        class="available-to-budget-page__muted"
                      >
                        ({{ record.provenance_label }})
                      </span>
                    </td>
                    <td v-if="showCategory">
                      {{ record.category_name ?? "—" }}
                    </td>
                    <td>{{ record.memo || "—" }}</td>
                    <td class="available-to-budget-page__number">
                      {{ signedAmount(record.contribution_minor) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="available-to-budget-page__count">
              Showing {{ records.length }} of {{ recordsTotal }} source
              entries<span v-if="recordsQuery.isFetchingNextPage.value">
                · Loading more...</span
              >
            </p>
            <div
              v-if="recordsQuery.isFetchNextPageError.value"
              class="available-to-budget-page__state available-to-budget-page__state--error"
              role="alert"
            >
              <p>More source entries could not be loaded.</p>
              <Button variant="secondary" @click="recordsQuery.fetchNextPage()"
                >Retry</Button
              >
            </div>
          </template>
          <CalculationFooter
            :label="`${group?.label ?? 'Selected group'} total`"
            :value="group ? formatCurrency(group.amount_minor) : '—'"
          />
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.available-to-budget-page {
  min-width: 0;
  background: var(--color-background);
}
.available-to-budget-page__main {
  display: grid;
  gap: var(--space-lg);
  align-content: start;
  padding: var(--space-page-block) var(--space-page-inline);
}
.available-to-budget-page__breadcrumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-primary);
  font: inherit;
  text-transform: uppercase;
}
.available-to-budget-page__breadcrumb button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-transform: inherit;
}
.available-to-budget-page__context,
.available-to-budget-page__surface {
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  border-radius: var(--radius-all);
}
.available-to-budget-page__context {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xl);
  padding: var(--space-md);
}
.available-to-budget-page__context > div {
  display: grid;
  gap: var(--space-xs);
}
.available-to-budget-page__label,
.available-to-budget-page__muted,
.available-to-budget-page__row small {
  color: var(--color-on-surface-muted);
}
.available-to-budget-page__label,
.available-to-budget-page__row small {
  font-size: var(--text-label-sm-font-size);
}
.available-to-budget-page__total {
  font: var(--text-metric-lg-font-weight) var(--text-metric-lg-font-size)
    var(--text-metric-lg-font-family);
  font-feature-settings: "tnum" 1;
}
.available-to-budget-page__surface {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-md);
}
.available-to-budget-page__section-heading {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  align-items: start;
}
.available-to-budget-page__section-heading h2,
.available-to-budget-page__section-heading p {
  margin: 0;
}
.available-to-budget-page__section-heading p,
.available-to-budget-page__arithmetic,
.available-to-budget-page__count {
  color: var(--color-on-surface-muted);
}
.available-to-budget-page__section-heading p {
  margin-top: var(--space-xs);
}
.available-to-budget-page__rows {
  display: grid;
  border-top: 1px solid var(--color-outline);
}
.available-to-budget-page__row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md);
  border: 0;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface);
  text-align: left;
  cursor: pointer;
}
.available-to-budget-page__row:hover,
.available-to-budget-page__row:focus-visible {
  background: var(--color-surface-selected);
}
.available-to-budget-page__row > span {
  display: grid;
  gap: var(--space-xs);
}
.available-to-budget-page__row--quiet {
  color: var(--color-on-surface-muted);
}
.available-to-budget-page__amount,
.available-to-budget-page__number {
  text-align: right;
  font-feature-settings: "tnum" 1;
}
.available-to-budget-page__empty {
  margin: 0;
  color: var(--color-on-surface-muted);
}
.available-to-budget-page__state {
  display: grid;
  gap: var(--space-sm);
  padding: var(--space-md);
  border: 1px solid var(--color-outline);
  background: var(--color-surface-muted);
}
.available-to-budget-page__state p {
  margin: 0;
}
.available-to-budget-page__state--error {
  border-color: var(--color-error);
}
.available-to-budget-page__ledger {
  box-sizing: border-box;
  height: clamp(320px, calc(100vh - 430px), 720px);
  overflow: auto;
  padding-block-end: var(--space-2xl);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
}
.available-to-budget-page__ledger table {
  display: grid;
  min-width: 720px;
  width: 100%;
}
.available-to-budget-page__ledger thead {
  position: sticky;
  top: 0;
  z-index: 1;
}
.available-to-budget-page__ledger tr {
  display: grid;
  grid-template-columns: 110px 1.1fr 1fr 1.4fr 130px;
}
.available-to-budget-page__ledger--without-category tr {
  grid-template-columns: 110px 1.1fr 1.4fr 130px;
}
.available-to-budget-page__ledger tbody {
  display: block;
  position: relative;
}
.available-to-budget-page__ledger tbody tr {
  position: absolute;
  inset-inline: 0;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface);
}
.available-to-budget-page__ledger th,
.available-to-budget-page__ledger td {
  padding: var(--space-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left;
}
.available-to-budget-page__ledger th {
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
  font-size: var(--text-label-sm-font-size);
}
.available-to-budget-page__ledger td {
  height: 52px;
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  line-height: var(--text-body-md-line-height);
}
.available-to-budget-page__count {
  margin: 0;
}
@media (max-width: 720px) {
  .available-to-budget-page__main {
    padding: var(--space-md);
  }
}
</style>
