<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { fetchAssetsLiabilities } from "@/dojo/api/client";
import Button from "@/dojo/components/actions/Button.vue";
import MetricStrip from "@/dojo/components/data/MetricStrip.vue";
import NavigationRail from "@/dojo/components/navigation/NavigationRail.vue";
import PageHeader from "@/dojo/components/data/PageHeader.vue";
import StateBadge from "@/dojo/components/display/StateBadge.vue";
import { formatCurrency } from "@/dojo/utils/currency";

const router = useRouter();

const navItems = computed(() => [
  {
    kind: "route" as const,
    key: "home",
    label: "Dashboard",
    icon: "dashboard",
    href: "/",
  },
  {
    kind: "route" as const,
    key: "budget",
    label: "Budget",
    icon: "budget",
    href: "/budgets",
  },
  {
    kind: "route" as const,
    key: "transactions",
    label: "Transactions",
    icon: "transactions",
    href: "/transactions",
  },
  {
    kind: "route" as const,
    key: "assets-liabilities",
    label: "Assets & Liabilities",
    icon: "assets",
    href: "/assets-liabilities",
    current: true,
  },
]);

const { data, isLoading } = useQuery({
  queryKey: ["assets-liabilities"],
  queryFn: fetchAssetsLiabilities,
});

const metricItems = computed(() => {
  if (!data.value) {
    return [
      { key: "net-worth", label: "Net worth", loading: true },
      { key: "assets", label: "Total assets", loading: true },
      { key: "liabilities", label: "Total liabilities", loading: true },
      { key: "change", label: "Change (30d)", loading: true },
    ];
  }

  return [
    {
      key: "net-worth",
      label: "Net worth",
      value: formatCurrency(data.value.net_worth_minor),
    },
    {
      key: "assets",
      label: "Total assets",
      value: formatCurrency(data.value.assets_minor),
    },
    {
      key: "liabilities",
      label: "Total liabilities",
      value: formatCurrency(data.value.liabilities_minor),
      status:
        data.value.liabilities_minor < 0
          ? { label: "", variant: "error" as const }
          : undefined,
    },
    {
      key: "change",
      label: "Change (30d)",
      value:
        data.value.change_30d_minor == null
          ? "—"
          : formatSignedCurrency(data.value.change_30d_minor),
    },
  ];
});

const groupLabels: Record<string, string> = {
  CASH: "Cash & equivalents",
  INVESTMENTS: "Investments",
  TANGIBLE_ASSETS: "Tangible assets",
  RESTRICTED_ASSETS: "Restricted assets",
  TRACKING_ASSETS: "Tracking assets",
  CREDIT: "Credit",
  LOANS: "Loans",
  TRACKING_LIABILITIES: "Tracking liabilities",
};

interface IconPart {
  tag: "path" | "rect" | "circle";
  attrs: Record<string, number | string>;
}

const groupIcons: Record<string, IconPart[]> = {
  CASH: [
    { tag: "rect", attrs: { x: 4, y: 7, width: 16, height: 10, rx: 1.5 } },
    { tag: "path", attrs: { d: "M7 12h.01M17 12h.01M4 10h16" } },
  ],
  INVESTMENTS: [
    { tag: "path", attrs: { d: "M5 17l4-4 3 2 5-7" } },
    { tag: "path", attrs: { d: "M17 8v5h-5" } },
    { tag: "path", attrs: { d: "M5 19h14" } },
  ],
  TANGIBLE_ASSETS: [
    { tag: "path", attrs: { d: "M4 11l8-6 8 6" } },
    { tag: "path", attrs: { d: "M6 10v9h12v-9" } },
    { tag: "path", attrs: { d: "M10 19v-5h4v5" } },
  ],
  RESTRICTED_ASSETS: [
    { tag: "rect", attrs: { x: 5, y: 10, width: 14, height: 10, rx: 2 } },
    { tag: "path", attrs: { d: "M8 10V7a4 4 0 018 0v3" } },
  ],
  TRACKING_ASSETS: [
    { tag: "path", attrs: { d: "M5 7h14M5 12h14M5 17h14" } },
    { tag: "circle", attrs: { cx: 7, cy: 7, r: 1 } },
    { tag: "circle", attrs: { cx: 7, cy: 12, r: 1 } },
    { tag: "circle", attrs: { cx: 7, cy: 17, r: 1 } },
  ],
  CREDIT: [
    { tag: "rect", attrs: { x: 4, y: 6, width: 16, height: 12, rx: 1.5 } },
    { tag: "path", attrs: { d: "M4 10h16M7 14h4" } },
  ],
  LOANS: [
    { tag: "path", attrs: { d: "M4 10h16L12 5 4 10z" } },
    { tag: "path", attrs: { d: "M6 10v7M10 10v7M14 10v7M18 10v7M4 19h16" } },
  ],
  TRACKING_LIABILITIES: [
    { tag: "path", attrs: { d: "M6 6h12v12H6z" } },
    { tag: "path", attrs: { d: "M9 10h6M9 14h4" } },
  ],
};

const collapsedGroups = ref<Set<string>>(new Set());

const toggleGroup = (key: string) => {
  if (collapsedGroups.value.has(key)) {
    collapsedGroups.value.delete(key);
  } else {
    collapsedGroups.value.add(key);
  }
};

const isGroupCollapsed = (key: string) => collapsedGroups.value.has(key);

const groupTestKey = (key: string) => key.toLowerCase().replace(/_/g, "-");

const handleAdd = () => {
  router.push("/assets-liabilities/add");
};

const handleRowSelect = (accountId: string) => {
  router.push(`/assets-liabilities/${accountId}`);
};

const formatAccountId = (item: {
  account_number_last4?: string | null;
  account_id: string;
}) => {
  if (item.account_number_last4) {
    return `•••• ${item.account_number_last4}`;
  }
  const last4 = item.account_id.slice(-4);
  return `•••• ${last4}`;
};

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return "—";
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const formatSignedCurrency = (amountMinor: number) => {
  const formatted = formatCurrency(Math.abs(amountMinor));
  if (amountMinor > 0) return `+${formatted}`;
  if (amountMinor < 0) return `-${formatted}`;
  return formatted;
};

const attention = (status: string) => {
  if (status === "CURRENT") {
    return { label: "OK", variant: "positive" as const };
  }
  if (status === "MISSING_VALUE") {
    return { label: "Missing value", variant: "error" as const };
  }
  if (status === "AWAITING_STATEMENT") {
    return { label: "Awaiting statement", variant: "warning" as const };
  }
  return { label: "Not reconciled", variant: "warning" as const };
};

const getSourceLabel = (source: string) => {
  const labels: Record<string, string> = {
    ledger: "System",
    valuation: "Valuation",
    manual: "Manual",
    snapshot: "Snapshot",
    imported_valuation: "Aspire",
    manual_valuation: "Manual",
    investment_statement: "Statement",
    loan_statement: "Statement",
  };
  return labels[source] || source;
};
</script>

<template>
  <div class="assets-liabilities-page" data-cy="assets-liabilities-page">
    <NavigationRail
      :items="navItems"
      :full-height="true"
      brand="dojo"
      aria-label="Main navigation"
    />

    <main class="assets-liabilities-page__main">
      <PageHeader title="Assets & Liabilities" :primary-actions="true">
        <template #actions>
          <Button @click="handleAdd">Add item</Button>
        </template>
      </PageHeader>

      <div data-cy="assets-liabilities-metrics">
        <MetricStrip
          :items="metricItems"
          class="assets-liabilities-page__metrics"
        />
      </div>

      <div
        v-if="isLoading"
        class="assets-liabilities-page__loading"
        data-cy="assets-liabilities-loading"
      >
        Loading...
      </div>

      <div
        v-else-if="data?.groups"
        class="assets-liabilities-page__groups"
        data-cy="assets-liabilities-groups"
      >
        <section
          v-for="group in data.groups"
          :key="group.key"
          class="assets-liabilities-page__group"
          data-cy="assets-liabilities-group"
          :data-group-key="groupTestKey(group.key)"
        >
          <button
            class="assets-liabilities-page__group-header"
            @click="toggleGroup(group.key)"
          >
            <div class="assets-liabilities-page__group-title-row">
              <span
                class="assets-liabilities-page__group-icon"
                aria-hidden="true"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <template
                    v-for="(part, index) in groupIcons[group.key]"
                    :key="index"
                  >
                    <component :is="part.tag" v-bind="part.attrs" />
                  </template>
                </svg>
              </span>
              <h2 class="assets-liabilities-page__group-title">
                {{ groupLabels[group.key] || group.key }}
              </h2>
              <span class="assets-liabilities-page__group-count">
                {{ group.items.length }} item{{
                  group.items.length !== 1 ? "s" : ""
                }}
              </span>
            </div>
            <div class="assets-liabilities-page__group-right">
              <span class="assets-liabilities-page__group-total-label">
                Total
              </span>
              <span class="assets-liabilities-page__group-total">
                {{ formatCurrency(group.total_minor) }}
              </span>
              <svg
                class="assets-liabilities-page__chevron"
                :class="{
                  'assets-liabilities-page__chevron--collapsed':
                    isGroupCollapsed(group.key),
                }"
                viewBox="0 0 16 16"
                fill="none"
              >
                <path
                  d="M4 6l4 4 4-4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
          </button>

          <div
            v-if="!isGroupCollapsed(group.key)"
            class="assets-liabilities-page__table"
          >
            <div class="assets-liabilities-page__table-header">
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--name"
                >Name</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--institution"
                >Institution</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--account"
                >Account / ID</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--balance"
                >Current balance / valuation</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--change"
                >Change (30d)</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--as-of"
                >As of</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--attention"
                >Attention</span
              >
              <span
                class="assets-liabilities-page__th assets-liabilities-page__th--actions"
              ></span>
            </div>

            <button
              v-for="item in group.items"
              :key="item.presentation_id ?? item.account_id"
              class="assets-liabilities-page__row"
              data-cy="assets-liabilities-row"
              @click="handleRowSelect(item.account_id)"
            >
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--name"
              >
                <span
                  class="assets-liabilities-page__status-dot"
                  :class="`assets-liabilities-page__status-dot--${item.source_of_truth}`"
                ></span>
                <span class="assets-liabilities-page__entity-name">
                  {{ item.name }}
                </span>
                <span class="assets-liabilities-page__entity-type">
                  {{ getSourceLabel(item.source_of_truth) }}
                </span>
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--institution"
              >
                {{ item.institution || "—" }}
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--account"
              >
                {{ formatAccountId(item) }}
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--balance"
                :class="{
                  'assets-liabilities-page__td--negative': item.value_minor < 0,
                }"
              >
                {{
                  item.attention_status === "AWAITING_STATEMENT"
                    ? "Awaiting statement"
                    : formatCurrency(item.value_minor)
                }}
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--change"
              >
                {{
                  item.change_30d_minor === null ||
                  item.change_30d_minor === undefined
                    ? "—"
                    : formatSignedCurrency(item.change_30d_minor)
                }}
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--as-of"
              >
                {{ formatDate(item.value_effective_date) }}
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--attention"
              >
                <StateBadge
                  :variant="attention(item.attention_status).variant"
                  size="sm"
                >
                  <svg
                    class="assets-liabilities-page__attention-icon"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <circle
                      cx="8"
                      cy="8"
                      r="6"
                      fill="currentColor"
                      opacity="0.15"
                    />
                    <path
                      d="M5.5 8l2 2 3.5-3.5"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  {{ attention(item.attention_status).label }}
                </StateBadge>
              </span>
              <span
                class="assets-liabilities-page__td assets-liabilities-page__td--actions"
              >
                <svg
                  class="assets-liabilities-page__kebab"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                >
                  <circle cx="8" cy="3" r="1.5" />
                  <circle cx="8" cy="8" r="1.5" />
                  <circle cx="8" cy="13" r="1.5" />
                </svg>
              </span>
            </button>
          </div>
        </section>
      </div>

      <div
        v-else
        class="assets-liabilities-page__empty"
        data-cy="assets-liabilities-empty"
      >
        <p>No accounts or assets configured yet.</p>
      </div>

      <p class="assets-liabilities-page__footer">All balances are in USD</p>
    </main>
  </div>
</template>

<style scoped>
.assets-liabilities-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.assets-liabilities-page__main {
  flex: 1;
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-page-block) var(--space-page-inline);
  min-width: 0;
  align-content: start;
}

.assets-liabilities-page__metrics {
  width: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
}

.assets-liabilities-page__loading {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-xl) 0;
}

.assets-liabilities-page__groups {
  display: grid;
  gap: var(--space-lg);
}

.assets-liabilities-page__group {
  display: grid;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  overflow: hidden;
}

.assets-liabilities-page__group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-surface);
  border: none;
  cursor: pointer;
  text-align: left;
  width: 100%;
}

.assets-liabilities-page__group-header:hover {
  background: var(--color-surface-selected);
}

.assets-liabilities-page__group-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.assets-liabilities-page__group-icon {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  flex-shrink: 0;
}

.assets-liabilities-page__group-icon svg {
  width: 20px;
  height: 20px;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.assets-liabilities-page__group-title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.assets-liabilities-page__group-count {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.assets-liabilities-page__group-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.assets-liabilities-page__group-total-label {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.assets-liabilities-page__group-total {
  color: var(--color-on-surface);
  font-family: var(--text-metric-md-font-family);
  font-size: var(--text-metric-md-font-size);
  font-weight: var(--text-metric-md-font-weight);
  line-height: var(--text-metric-md-line-height);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.assets-liabilities-page__chevron {
  width: 16px;
  height: 16px;
  color: var(--color-on-surface-muted);
  transition: transform var(--transition-fast) var(--ease-out);
}

.assets-liabilities-page__chevron--collapsed {
  transform: rotate(-90deg);
}

.assets-liabilities-page__table {
  border-top: 1px solid var(--color-outline);
}

.assets-liabilities-page__table-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 1.2fr 1fr 0.8fr 1fr 40px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-outline);
}

.assets-liabilities-page__th {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.assets-liabilities-page__th--balance,
.assets-liabilities-page__th--change {
  text-align: right;
}

.assets-liabilities-page__row {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 1.2fr 1fr 0.8fr 1fr 40px;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-surface);
  border: none;
  border-bottom: 1px solid var(--color-outline);
  cursor: pointer;
  text-align: left;
  width: 100%;
  align-items: center;
}

.assets-liabilities-page__row:last-child {
  border-bottom: none;
}

.assets-liabilities-page__row:hover {
  background: var(--color-surface-selected);
}

.assets-liabilities-page__td {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  min-width: 0;
}

.assets-liabilities-page__td--name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.assets-liabilities-page__status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-positive);
}

.assets-liabilities-page__status-dot--valuation {
  background: var(--color-positive);
}

.assets-liabilities-page__status-dot--manual {
  background: var(--color-warning);
}

.assets-liabilities-page__entity-name {
  font-weight: 600;
}

.assets-liabilities-page__entity-type {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.assets-liabilities-page__td--institution {
  color: var(--color-on-surface);
}

.assets-liabilities-page__td--account {
  color: var(--color-on-surface-muted);
  font-family: var(--text-numeric-font-family);
  font-size: var(--text-numeric-font-size);
  font-weight: var(--text-numeric-font-weight);
  line-height: var(--text-numeric-line-height);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.assets-liabilities-page__td--balance {
  text-align: right;
  font-weight: 600;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.assets-liabilities-page__td--negative {
  color: var(--color-error);
}

.assets-liabilities-page__td--change {
  text-align: right;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.assets-liabilities-page__td--as-of {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.assets-liabilities-page__td--attention {
  display: flex;
  align-items: center;
}

.assets-liabilities-page__attention-icon {
  width: 14px;
  height: 14px;
}

.assets-liabilities-page__td--actions {
  display: flex;
  align-items: center;
  justify-content: center;
}

.assets-liabilities-page__kebab {
  width: 16px;
  height: 16px;
  color: var(--color-on-surface-muted);
}

.assets-liabilities-page__empty {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-2xl) 0;
  text-align: center;
}

.assets-liabilities-page__empty-hint {
  margin-top: var(--space-sm);
  font-style: italic;
}

.assets-liabilities-page__footer {
  margin: 0;
  padding: var(--space-lg) 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  text-align: center;
}

@media (max-width: 900px) {
  .assets-liabilities-page__table-header,
  .assets-liabilities-page__row {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xs);
  }

  .assets-liabilities-page__th--institution,
  .assets-liabilities-page__th--account,
  .assets-liabilities-page__th--change,
  .assets-liabilities-page__th--as-of,
  .assets-liabilities-page__th--actions,
  .assets-liabilities-page__td--institution,
  .assets-liabilities-page__td--account,
  .assets-liabilities-page__td--change,
  .assets-liabilities-page__td--as-of,
  .assets-liabilities-page__td--actions {
    display: none;
  }
}
</style>
