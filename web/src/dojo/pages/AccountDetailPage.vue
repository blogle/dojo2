<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchAccounts, fetchTransactionsPage } from "@/dojo/api/client";
import Button from "@/dojo/components/actions/Button.vue";
import DropdownButton from "@/dojo/components/actions/DropdownButton.vue";
import MetricStrip from "@/dojo/components/data/MetricStrip.vue";
import type { MetricStripItem } from "@/dojo/components/data/MetricStrip.vue";
import PageHeader from "@/dojo/components/data/PageHeader.vue";
import KeyValueList from "@/dojo/components/display/KeyValueList.vue";
import type { KeyValueItem } from "@/dojo/components/display/KeyValueList.vue";
import StateBadge from "@/dojo/components/display/StateBadge.vue";
import type { StateBadgeVariant } from "@/dojo/components/display/StateBadge.vue";
import NavigationRail from "@/dojo/components/navigation/NavigationRail.vue";
import { formatCurrency } from "@/dojo/utils/currency";

const route = useRoute();
const router = useRouter();
const accountId = computed(() => route.params.id as string);

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

const { data: accounts, isLoading: accountsLoading } = useQuery({
  queryKey: ["accounts"],
  queryFn: () => fetchAccounts(false),
});

const account = computed(() =>
  accounts.value?.find((a) => a.account_id === accountId.value),
);

const { data: txPage, isLoading: txLoading } = useQuery({
  queryKey: ["transactions", accountId.value],
  queryFn: () => fetchTransactionsPage(false, 0, 50),
  enabled: computed(() => !!accountId.value),
});

const transactions = computed(
  () =>
    txPage.value?.items.filter((t) => t.account_id === accountId.value) ?? [],
);

const isBudgetAccount = computed(
  () => account.value?.account_class === "BUDGET",
);
const isInvestmentAccount = computed(
  () => account.value?.account_class === "INVESTMENT",
);
const isLoanAccount = computed(() => account.value?.account_class === "LOAN");
const isTrackingAccount = computed(
  () => account.value?.account_class === "TRACKING",
);
const isTangibleAsset = computed(
  () => account.value?.account_class === "TANGIBLE_ASSET",
);

const pageTitle = computed(() => account.value?.name ?? "Account");

const accountTypeBadge = computed(() => {
  if (!account.value) return null;
  if (isBudgetAccount.value)
    return { label: "Budget account", variant: "info" as const };
  if (isInvestmentAccount.value)
    return { label: "Investment account", variant: "info" as const };
  if (isLoanAccount.value) return { label: "Loan", variant: "info" as const };
  if (isTrackingAccount.value)
    return { label: "Tracking account", variant: "info" as const };
  if (isTangibleAsset.value)
    return { label: "Tangible asset", variant: "info" as const };
  return { label: account.value.account_class, variant: "info" as const };
});

const ledgerBadge = computed(() => {
  if (!account.value) return null;
  if (isBudgetAccount.value) return "Ledger";
  if (isInvestmentAccount.value) return "Investment activity + valuation";
  if (isLoanAccount.value) return "Loan balance";
  if (isTrackingAccount.value) return "Snapshot";
  return null;
});

const metricItems = computed((): MetricStripItem[] => {
  if (!account.value) {
    return Array.from({ length: 5 }, (_, i) => ({
      key: `m${i}`,
      label: "...",
      loading: true,
    }));
  }

  if (isBudgetAccount.value) {
    return [
      {
        key: "balance",
        label: "Current balance",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: `As of ${formatDateShort()}`,
      },
      {
        key: "pending",
        label: "Pending",
        value: formatCurrency(account.value.pending_balance_minor),
        auxValue: `${transactions.value.filter((t) => t.status === "PENDING").length} transactions`,
      },
      {
        key: "cleared",
        label: "Cleared",
        value: formatCurrency(account.value.cleared_balance_minor),
        auxValue: `${transactions.value.filter((t) => t.status === "CLEARED").length} transactions`,
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: "Assets",
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Up to date",
        auxValue: `As of ${formatDateShort()}`,
        status: { label: "", variant: "positive" as const },
      },
    ];
  }

  if (isInvestmentAccount.value) {
    return [
      {
        key: "value",
        label: "Current value",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: `As of ${formatDateShort()}`,
      },
      {
        key: "cash",
        label: "Cash",
        value: formatCurrency(account.value.cleared_balance_minor),
        auxValue: `As of ${formatDateShort()}`,
      },
      {
        key: "holdings",
        label: "Holdings value",
        value: formatCurrency(
          account.value.display_balance_minor -
            account.value.cleared_balance_minor,
        ),
        auxValue: `As of ${formatDateShort()}`,
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: "Asset",
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Up to date",
        auxValue: `As of ${formatDateShort()}`,
        status: { label: "", variant: "positive" as const },
      },
    ];
  }

  if (isLoanAccount.value) {
    return [
      {
        key: "obligation",
        label: "Current obligation",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: `Due on ${formatDateShort()}`,
      },
      {
        key: "balance",
        label: "Principal balance",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: `As of ${formatDateShort()}`,
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: "Liability",
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Up to date",
        auxValue: `As of ${formatDateShort()}`,
        status: { label: "", variant: "positive" as const },
      },
    ];
  }

  return [
    {
      key: "value",
      label: "Current value",
      value: formatCurrency(account.value.display_balance_minor),
      auxValue: `As of ${formatDateShort()}`,
    },
    {
      key: "net-worth",
      label: "Net worth contribution",
      value: formatCurrency(account.value.display_balance_minor),
      auxValue: isTrackingAccount.value ? "Asset" : "Assets",
    },
    {
      key: "recon",
      label: "Reconciliation freshness",
      value: "Up to date",
      auxValue: `As of ${formatDateShort()}`,
      status: { label: "", variant: "positive" as const },
    },
  ];
});

const accountDetails = computed((): KeyValueItem[] => {
  if (!account.value) return [];
  const items: KeyValueItem[] = [
    {
      label: "Account type",
      value: accountTypeBadge.value?.label ?? account.value.account_class,
    },
    {
      label: "Account / ID",
      value: `•••• ${account.value.account_id.slice(-4)}`,
    },
  ];
  if (isBudgetAccount.value) {
    items.push({ label: "Ledger", value: "Cash & equivalents" });
    items.push({ label: "Budget category", value: "System" });
  }
  items.push({
    label: "Current balance",
    value: formatCurrency(account.value.display_balance_minor),
  });
  return items;
});

const reconciliationDetails = computed((): KeyValueItem[] => [
  { label: "Status", value: "Up to date", variant: "positive" },
  { label: "Last reconciled", value: formatDateShort() },
]);

const historyDetails = computed((): KeyValueItem[] => {
  if (!account.value) return [];
  return [
    { label: "Date opened", value: "Jan 10, 2020" },
    { label: "Imported since", value: "Jan 10, 2020" },
    { label: "Total transactions", value: String(transactions.value.length) },
  ];
});

const configurationDetails = computed((): KeyValueItem[] => [
  { label: "Active", value: "Yes", variant: "positive" },
  { label: "Include in net worth", value: "Yes", variant: "positive" },
]);

const transactionColumns = computed(() => {
  if (isInvestmentAccount.value) {
    return [
      { key: "date", label: "Date" },
      { key: "category", label: "Category / Memo" },
      { key: "amount", label: "Amount", align: "end" as const },
      { key: "status", label: "Status" },
      { key: "balance", label: "Balance", align: "end" as const },
    ];
  }
  return [
    { key: "date", label: "Date" },
    { key: "description", label: "Description" },
    { key: "category", label: "Category" },
    { key: "amount", label: "Amount", align: "end" as const },
    { key: "status", label: "Status" },
    { key: "balance", label: "Balance", align: "end" as const },
  ];
});

const transactionRows = computed(() => {
  let runningBalance = account.value?.display_balance_minor ?? 0;
  const sorted = [...transactions.value].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
  );
  return sorted.map((t) => {
    runningBalance -= t.amount_minor;
    return {
      key: t.transaction_id,
      date: formatDateFull(t.date),
      description: t.memo || t.account_name,
      category: t.category_name ?? t.system_category ?? "—",
      amount: formatCurrency(t.amount_minor),
      amountClass: t.amount_minor < 0 ? "text-error" : "text-positive",
      status: t.status === "CLEARED" ? "Cleared" : "Pending",
      statusVariant: (t.status === "CLEARED"
        ? "positive"
        : "warning") as StateBadgeVariant,
      statusIcon: (t.status === "CLEARED" ? "check" : "clock") as string,
      balance: formatCurrency(runningBalance),
    };
  });
});

const moreActions = computed(() => {
  const actions = [{ key: "history", label: "View history" }];
  if (isBudgetAccount.value) {
    actions.unshift({ key: "reconcile", label: "Reconcile" });
  }
  if (isInvestmentAccount.value) {
    actions.unshift(
      { key: "contribute", label: "Contribute" },
      { key: "withdraw", label: "Withdraw" },
      { key: "reconcile", label: "Reconcile" },
    );
  }
  if (isLoanAccount.value) {
    actions.unshift(
      { key: "record-payment", label: "Record payment" },
      { key: "reconcile", label: "Reconcile" },
      { key: "edit-loan", label: "Edit loan" },
    );
  }
  return actions;
});

const handleBack = () => {
  router.push("/assets-liabilities");
};

const handleMoreAction = (key: string) => {
  if (key === "reconcile") {
    router.push("/assets-liabilities");
  }
};

function formatDateShort(): string {
  return new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateFull(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
</script>

<template>
  <div class="account-detail-page" data-cy="account-detail-page">
    <NavigationRail
      :items="navItems"
      :full-height="true"
      brand="dojo"
      aria-label="Main navigation"
    />

    <main class="account-detail-page__main">
      <div v-if="accountsLoading" class="account-detail-page__loading">
        Loading...
      </div>

      <template v-else-if="account">
        <nav class="account-detail-page__back">
          <button class="account-detail-page__back-link" @click="handleBack">
            <svg
              viewBox="0 0 16 16"
              fill="none"
              class="account-detail-page__back-icon"
            >
              <path
                d="M10 3L5 8l5 5"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Back to Assets & Liabilities
          </button>
        </nav>

        <PageHeader :title="pageTitle" :primary-actions="true">
          <template #title>
            <span class="account-detail-page__title-text">{{ pageTitle }}</span>
          </template>
          <template v-if="accountTypeBadge || ledgerBadge" #eyebrow>
            <span class="account-detail-page__badges">
              <StateBadge
                v-if="accountTypeBadge"
                :variant="accountTypeBadge.variant"
                size="sm"
              >
                {{ accountTypeBadge.label }}
              </StateBadge>
              <StateBadge v-if="ledgerBadge" variant="info" size="sm">
                {{ ledgerBadge }}
              </StateBadge>
            </span>
          </template>
          <template #actions>
            <DropdownButton
              v-if="moreActions.length > 1"
              :label="moreActions[0]?.label ?? 'Actions'"
              :items="moreActions.slice(1)"
              @select="handleMoreAction"
            />
            <Button
              v-else-if="moreActions.length === 1"
              variant="secondary"
              @click="handleMoreAction(moreActions[0].key)"
            >
              {{ moreActions[0].label }}
            </Button>
          </template>
        </PageHeader>

        <MetricStrip
          :items="metricItems"
          class="account-detail-page__metrics"
        />

        <div class="account-detail-page__content">
          <div class="account-detail-page__left">
            <section
              class="account-detail-page__section"
              data-cy="transactions-section"
            >
              <div class="account-detail-page__section-header">
                <svg
                  class="account-detail-page__section-icon"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <rect
                    x="2"
                    y="2"
                    width="12"
                    height="12"
                    rx="2"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <path
                    d="M5 6h6M5 8h4M5 10h5"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
                <h2 class="account-detail-page__section-title">
                  {{
                    isInvestmentAccount
                      ? "Contribution & withdrawal activity"
                      : isLoanAccount
                        ? "Payment activity"
                        : "Transactions"
                  }}
                </h2>
                <span class="account-detail-page__section-count">
                  {{ transactions.length }} transaction{{
                    transactions.length !== 1 ? "s" : ""
                  }}
                </span>
              </div>

              <div v-if="txLoading" class="account-detail-page__tx-loading">
                Loading transactions...
              </div>

              <div v-else class="account-detail-page__table">
                <div class="account-detail-page__table-header">
                  <span
                    v-for="col in transactionColumns"
                    :key="col.key"
                    class="account-detail-page__th"
                    :class="{
                      'account-detail-page__th--end': col.align === 'end',
                    }"
                  >
                    {{ col.label }}
                  </span>
                </div>

                <div
                  v-for="row in transactionRows"
                  :key="row.key"
                  class="account-detail-page__row"
                >
                  <span class="account-detail-page__td">
                    {{ row.date }}
                  </span>
                  <span
                    v-if="!isInvestmentAccount"
                    class="account-detail-page__td"
                  >
                    {{ row.description }}
                  </span>
                  <span class="account-detail-page__td">
                    {{ row.category }}
                  </span>
                  <span
                    class="account-detail-page__td account-detail-page__td--end"
                    :class="row.amountClass"
                  >
                    {{ row.amount }}
                  </span>
                  <span class="account-detail-page__td">
                    <StateBadge
                      :variant="row.statusVariant"
                      size="sm"
                      :icon="row.statusIcon"
                    >
                      {{ row.status }}
                    </StateBadge>
                  </span>
                  <span
                    class="account-detail-page__td account-detail-page__td--end"
                  >
                    {{ row.balance }}
                  </span>
                </div>

                <div
                  v-if="transactionRows.length === 0"
                  class="account-detail-page__empty"
                >
                  No transactions found.
                </div>

                <div
                  v-else-if="txPage?.has_more"
                  class="account-detail-page__scroll-hint"
                >
                  Loaded {{ transactions.length }} of {{ txPage.total }}
                  transactions • scroll to load more
                </div>
              </div>
            </section>

            <section
              class="account-detail-page__section"
              data-cy="chart-section"
            >
              <h2 class="account-detail-page__section-title">
                {{
                  isInvestmentAccount
                    ? "Value over time"
                    : isLoanAccount
                      ? "Loan balance over time"
                      : "Balance over time"
                }}
              </h2>
              <div class="account-detail-page__chart-placeholder">
                <div class="account-detail-page__chart-value">
                  {{ formatCurrency(account.display_balance_minor) }}
                </div>
                <p class="account-detail-page__chart-sub">
                  As of {{ formatDateShort() }}
                </p>
                <div class="account-detail-page__chart-empty">
                  Chart will render here
                </div>
              </div>
            </section>
          </div>

          <aside class="account-detail-page__sidebar">
            <section
              class="account-detail-page__sidebar-section"
              data-cy="account-details-section"
            >
              <div class="account-detail-page__sidebar-header">
                <h3 class="account-detail-page__sidebar-title">
                  Account details
                </h3>
                <svg
                  class="account-detail-page__sidebar-icon"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <rect
                    x="2"
                    y="2"
                    width="12"
                    height="12"
                    rx="2"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <path
                    d="M5 8h6M8 5v6"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
              </div>
              <KeyValueList :items="accountDetails" />
              <button class="account-detail-page__sidebar-link">
                View budgeting details
              </button>
            </section>

            <section
              class="account-detail-page__sidebar-section"
              data-cy="reconciliation-section"
            >
              <h3 class="account-detail-page__sidebar-title">Reconciliation</h3>
              <KeyValueList :items="reconciliationDetails" />
            </section>

            <section
              class="account-detail-page__sidebar-section"
              data-cy="history-section"
            >
              <h3 class="account-detail-page__sidebar-title">History</h3>
              <KeyValueList :items="historyDetails" />
            </section>

            <section
              class="account-detail-page__sidebar-section"
              data-cy="configuration-section"
            >
              <h3 class="account-detail-page__sidebar-title">Configuration</h3>
              <KeyValueList :items="configurationDetails" />
              <button class="account-detail-page__sidebar-link">
                Edit configuration
              </button>
            </section>
          </aside>
        </div>
      </template>

      <div v-else class="account-detail-page__not-found">
        <p>Account not found.</p>
        <Button variant="secondary" @click="handleBack">
          Back to Assets & Liabilities
        </Button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.account-detail-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.account-detail-page__main {
  flex: 1;
  display: grid;
  gap: var(--space-lg);
  padding: var(--space-page-block) var(--space-page-inline);
  min-width: 0;
  align-content: start;
}

.account-detail-page__loading {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-xl) 0;
}

.account-detail-page__back {
  margin-bottom: var(--space-sm);
}

.account-detail-page__back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-primary);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  padding: 0;
}

.account-detail-page__back-link:hover {
  text-decoration: underline;
}

.account-detail-page__back-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.account-detail-page__title-text {
  display: inline;
}

.account-detail-page__badges {
  display: inline-flex;
  gap: var(--space-sm);
  align-items: center;
}

.account-detail-page__metrics {
  width: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
}

.account-detail-page__content {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-lg);
}

.account-detail-page__left {
  display: grid;
  gap: var(--space-lg);
  min-width: 0;
}

.account-detail-page__section {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  overflow: hidden;
}

.account-detail-page__section-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
}

.account-detail-page__section-icon {
  width: 16px;
  height: 16px;
  color: var(--color-on-surface-muted);
  flex-shrink: 0;
}

.account-detail-page__section-title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.account-detail-page__section-count {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__tx-loading {
  padding: var(--space-xl);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

.account-detail-page__table {
  width: 100%;
}

.account-detail-page__table-header {
  display: grid;
  grid-template-columns: 90px 2fr 120px 85px 85px 90px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-outline);
}

.account-detail-page__th {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.account-detail-page__th--end {
  text-align: right;
}

.account-detail-page__row {
  display: grid;
  grid-template-columns: 90px 2fr 120px 85px 85px 90px;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  align-items: center;
}

.account-detail-page__row:last-child {
  border-bottom: none;
}

.account-detail-page__row:hover {
  background: var(--color-surface-selected);
}

.account-detail-page__td {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-detail-page__td--end {
  text-align: right;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.account-detail-page__empty {
  padding: var(--space-xl);
  color: var(--color-on-surface-muted);
  text-align: center;
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

.account-detail-page__scroll-hint {
  padding: var(--space-md) var(--space-lg);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
  border-top: 1px solid var(--color-outline);
}

.text-positive {
  color: var(--color-positive);
  font-weight: 600;
}

.text-error {
  color: var(--color-error);
  font-weight: 600;
}

.account-detail-page__chart-placeholder {
  padding: var(--space-xl);
}

.account-detail-page__chart-value {
  color: var(--color-on-surface);
  font-family: var(--text-headline-md-font-family);
  font-size: var(--text-headline-md-font-size);
  font-weight: var(--text-headline-md-font-weight);
  line-height: var(--text-headline-md-line-height);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.account-detail-page__chart-sub {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  margin: var(--space-xs) 0 var(--space-lg);
}

.account-detail-page__chart-empty {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--color-outline);
  border-radius: var(--radius-all);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.account-detail-page__sidebar {
  display: grid;
  gap: var(--space-lg);
  align-content: start;
}

.account-detail-page__sidebar-section {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  padding: var(--space-lg);
}

.account-detail-page__sidebar-title {
  margin: 0 0 var(--space-md);
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.account-detail-page__sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.account-detail-page__sidebar-header .account-detail-page__sidebar-title {
  margin-bottom: 0;
}

.account-detail-page__sidebar-icon {
  width: 16px;
  height: 16px;
  color: var(--color-on-surface-muted);
}

.account-detail-page__sidebar-link {
  display: block;
  width: 100%;
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  cursor: pointer;
  text-align: center;
  color: var(--color-on-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__sidebar-link:hover {
  background: var(--color-surface-selected);
}

.account-detail-page__not-found {
  display: grid;
  gap: var(--space-lg);
  justify-items: center;
  padding: var(--space-3xl) 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

@media (max-width: 900px) {
  .account-detail-page__content {
    grid-template-columns: 1fr;
  }

  .account-detail-page__table-header,
  .account-detail-page__row {
    grid-template-columns: 80px 1fr 80px;
    gap: var(--space-xs);
  }

  .account-detail-page__th:nth-child(2),
  .account-detail-page__th:nth-child(5),
  .account-detail-page__th:nth-child(6),
  .account-detail-page__td:nth-child(2),
  .account-detail-page__td:nth-child(5),
  .account-detail-page__td:nth-child(6) {
    display: none;
  }
}
</style>
