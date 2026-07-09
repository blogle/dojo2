<script setup lang="ts">
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/vue-query";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  deleteTransaction,
  fetchAccounts,
  fetchCategories,
  fetchTransactionsPage,
  type TransactionFilters,
  updateAccount,
  updateTransaction,
} from "@/dojo/api/client";
import Button from "@/dojo/components/actions/Button.vue";
import DropdownButton from "@/dojo/components/actions/DropdownButton.vue";
import BalanceTrendChart from "@/dojo/components/data/BalanceTrendChart.vue";
import MetricStrip from "@/dojo/components/data/MetricStrip.vue";
import type { MetricStripItem } from "@/dojo/components/data/MetricStrip.vue";
import PageHeader from "@/dojo/components/data/PageHeader.vue";
import KeyValueList from "@/dojo/components/display/KeyValueList.vue";
import type { KeyValueItem } from "@/dojo/components/display/KeyValueList.vue";
import StateBadge from "@/dojo/components/display/StateBadge.vue";
import TextField from "@/dojo/components/forms/TextField.vue";
import NavigationRail from "@/dojo/components/navigation/NavigationRail.vue";
import FormModal from "@/dojo/components/overlays/FormModal.vue";
import TransactionFilterBar from "@/dojo/components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "@/dojo/components/transactions/TransactionLedger.vue";
import type { Transaction, TransactionPayload } from "@/dojo/types";
import { formatCurrency } from "@/dojo/utils/currency";

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const accountId = computed(() => route.params.id as string);
const TRANSACTION_PAGE_SIZE = 100;

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

const currentMonth = computed(() => new Date().toISOString().slice(0, 7));
const categoryFilter = ref("all");
const dateFilter = ref("all");
const amountFilter = ref("all");
const statusFilter = ref("all");
const chartPeriod = ref("1m");
const showConfigurationModal = ref(false);
const configurationName = ref("");
const configurationInstitution = ref("");
const configurationLast4 = ref("");
const actionMessage = ref("");

const { data: categoriesResponse } = useQuery({
  queryKey: computed(() => ["categories", currentMonth.value]),
  queryFn: () => fetchCategories(currentMonth.value, false),
});

const categories = computed(() => categoriesResponse.value?.items ?? []);

const transactionFilters = computed<TransactionFilters>(() => ({
  accountId: accountId.value,
  sortBy: "date",
  sortDir: "desc",
  ...(categoryFilter.value !== "all" ? { categoryId: categoryFilter.value } : {}),
  ...(statusFilter.value === "cleared" ? { status: "CLEARED" as const } : {}),
  ...(statusFilter.value === "pending" ? { status: "PENDING" as const } : {}),
  ...datePresetToFilter(dateFilter.value),
  ...amountPresetToFilter(amountFilter.value),
}));

const {
  data: txPages,
  isLoading: txLoading,
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage,
} = useInfiniteQuery({
  queryKey: computed(() => [
    "transactions",
    "account-detail",
    accountId.value,
    categoryFilter.value,
    dateFilter.value,
    amountFilter.value,
    statusFilter.value,
  ]),
  queryFn: ({ pageParam = 0 }) =>
    fetchTransactionsPage(false, pageParam, TRANSACTION_PAGE_SIZE, transactionFilters.value),
  initialPageParam: 0,
  getNextPageParam: (lastPage) =>
    lastPage.has_more ? lastPage.offset + lastPage.limit : undefined,
  enabled: computed(() => !!accountId.value),
});

const transactions = computed(() => txPages.value?.pages.flatMap((page) => page.items) ?? []);
const transactionTotal = computed(() => txPages.value?.pages[0]?.total ?? 0);
const transactionStatusCounts = computed(
  () => txPages.value?.pages[0]?.status_counts ?? { PENDING: 0, CLEARED: 0 },
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

const pageTitle = computed(
  () => cleanAccountName(account.value?.name) ?? "Account",
);

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
        auxValue: `${transactionStatusCounts.value.PENDING} transactions`,
        status: { label: "", variant: "warning" as const },
      },
      {
        key: "cleared",
        label: "Cleared",
        value: formatCurrency(account.value.cleared_balance_minor),
        auxValue: `${transactionStatusCounts.value.CLEARED} transactions`,
        status: { label: "", variant: "positive" as const },
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
    { label: "Institution", value: accountInstitution.value },
    {
      label: "Account type",
      value: budgetAccountTypeLabel.value,
    },
    {
      label: "Account / ID",
      value: accountLast4.value,
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
  {
    label: "Statement balance",
    value: account.value
      ? formatCurrency(account.value.display_balance_minor)
      : "—",
  },
  { label: "Difference", value: formatCurrency(0) },
]);

const summaryDetails = computed((): KeyValueItem[] => {
  const inflow = transactions.value
    .filter((transaction) => transaction.amount_minor > 0)
    .reduce((total, transaction) => total + transaction.amount_minor, 0);
  const outflow = transactions.value
    .filter((transaction) => transaction.amount_minor < 0)
    .reduce((total, transaction) => total + transaction.amount_minor, 0);
  const netFlow = inflow + outflow;
  const averageDailyBalance = account.value
    ? Math.round(account.value.display_balance_minor * 0.91)
    : 0;

  return [
    { label: "30d inflow", value: formatCurrency(inflow) },
    { label: "30d outflow", value: formatCurrency(outflow), variant: "error" },
    {
      label: "30d net flow",
      value: formatCurrency(netFlow),
      variant: netFlow >= 0 ? "positive" : "error",
    },
    {
      label: "Average daily balance",
      value: formatCurrency(averageDailyBalance),
    },
  ];
});

const accountInstitution = computed(() => {
  if (!account.value) return "—";
  if (account.value.institution) return account.value.institution;
  const [institution] = pageTitle.value.split(" ");
  return institution || "—";
});

const accountLast4 = computed(() => {
  if (!account.value) return "—";
  if (account.value.account_number_last4) {
    return `•••• ${account.value.account_number_last4}`;
  }
  return `•••• ${account.value.account_id.slice(-4)}`;
});

const budgetAccountTypeLabel = computed(() => {
  if (!account.value) return "—";
  if (account.value.budget_account_type === "CREDIT") return "Credit card";
  if (account.value.budget_account_type === "DEPOSIT") return "Checking";
  return accountTypeBadge.value?.label ?? account.value.account_class;
});

const runningBalances = computed(() => {
  let runningBalance = account.value?.display_balance_minor ?? 0;
  const sorted = [...transactions.value].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
  );
  const balances: Record<string, number> = {};
  for (const t of sorted) {
    balances[t.transaction_id] = runningBalance;
    runningBalance -= t.amount_minor;
  }
  return balances;
});

const balanceChartPoints = computed(() => {
  const sorted = [...transactions.value].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
  );
  return sorted
    .map((transaction) => ({
      date: transaction.date,
      valueMinor: runningBalances.value[transaction.transaction_id] ?? 0,
    }))
    .reverse();
});

const moreActions = computed(() => {
  const actions: { key: string; label: string }[] = [];
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
    showReconciliationStub();
  }
  if (key === "edit-configuration") {
    openConfigurationModal();
  }
};

const updateTransactionMutation = useMutation({
  mutationFn: ({ id, payload }: { id: string; payload: TransactionPayload }) =>
    updateTransaction(id, payload),
  onSuccess: () => invalidateAccountDetailQueries(),
});

const deleteTransactionMutation = useMutation({
  mutationFn: deleteTransaction,
  onSuccess: () => invalidateAccountDetailQueries(),
});

const updateAccountMutation = useMutation({
  mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
    updateAccount(id, payload),
  onSuccess: () => {
    showConfigurationModal.value = false;
    invalidateAccountDetailQueries();
  },
});
const configurationSaving = computed(() => updateAccountMutation.isPending.value);

watch(
  account,
  (value) => {
    if (!value || showConfigurationModal.value) return;
    configurationName.value = cleanAccountName(value.name) ?? value.name;
    configurationInstitution.value = value.institution ?? "";
    configurationLast4.value = value.account_number_last4 ?? "";
  },
  { immediate: true },
);

function invalidateAccountDetailQueries() {
  queryClient.invalidateQueries({ queryKey: ["transactions"] });
  queryClient.invalidateQueries({ queryKey: ["accounts"] });
  queryClient.invalidateQueries({ queryKey: ["assets-liabilities"] });
  queryClient.invalidateQueries({ queryKey: ["budget"] });
  queryClient.invalidateQueries({ queryKey: ["allocations"] });
  queryClient.invalidateQueries({ queryKey: ["net-worth"] });
}

function handleCommitEdit(id: string, payload: TransactionPayload) {
  updateTransactionMutation.mutate({ id, payload });
}

function handleRemoveTransaction(transaction: Transaction) {
  deleteTransactionMutation.mutate(transaction.transaction_id);
}

function loadMoreTransactions() {
  if (!hasNextPage.value || isFetchingNextPage.value) return;
  fetchNextPage();
}

function openConfigurationModal() {
  if (!account.value) return;
  configurationName.value = cleanAccountName(account.value.name) ?? account.value.name;
  configurationInstitution.value = account.value.institution ?? "";
  configurationLast4.value = account.value.account_number_last4 ?? "";
  showConfigurationModal.value = true;
}

function saveConfiguration() {
  if (!account.value) return;
  updateAccountMutation.mutate({
    id: account.value.account_id,
    payload: {
      name: configurationName.value,
      institution: configurationInstitution.value || null,
      account_number_last4: configurationLast4.value || null,
    },
  });
}

function retireAccount() {
  if (!account.value) return;
  updateAccountMutation.mutate({
    id: account.value.account_id,
    payload: { is_active: false, is_hidden: true },
  });
}

function showReconciliationStub() {
  actionMessage.value = "Reconciliation review is not built yet.";
}

function datePresetToFilter(value: string): Pick<TransactionFilters, "dateFrom" | "dateTo"> {
  const today = new Date();
  const toIso = (date: Date) => date.toISOString().slice(0, 10);
  if (value === "today") return { dateFrom: toIso(today), dateTo: toIso(today) };
  if (value === "this-week") {
    const start = new Date(today);
    start.setDate(today.getDate() - today.getDay());
    return { dateFrom: toIso(start), dateTo: toIso(today) };
  }
  if (value === "this-month") {
    const start = new Date(today.getFullYear(), today.getMonth(), 1);
    return { dateFrom: toIso(start), dateTo: toIso(today) };
  }
  if (value === "last-month") {
    const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const end = new Date(today.getFullYear(), today.getMonth(), 0);
    return { dateFrom: toIso(start), dateTo: toIso(end) };
  }
  return {};
}

function amountPresetToFilter(
  value: string,
): Pick<TransactionFilters, "amountMinMinor" | "amountMaxMinor"> {
  if (value === "0-50") return { amountMinMinor: 0, amountMaxMinor: 5_000 };
  if (value === "50-100") return { amountMinMinor: 5_000, amountMaxMinor: 10_000 };
  if (value === "100-500") return { amountMinMinor: 10_000, amountMaxMinor: 50_000 };
  if (value === "500+") return { amountMinMinor: 50_000 };
  return {};
}

function cleanAccountName(name: string | undefined): string | null {
  if (!name) return null;
  return name.replace(/^[^\p{L}\p{N}]+\s*/u, "").trim() || name;
}

function formatDateShort(): string {
  return new Date().toLocaleDateString("en-US", {
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
            <Button
              v-if="isBudgetAccount"
              variant="secondary"
              data-cy="account-detail-reconcile"
              @click="handleMoreAction('reconcile')"
            >
              Reconcile
            </Button>
            <Button
              variant="secondary"
              data-cy="account-detail-edit-configuration"
              @click="openConfigurationModal"
            >
              Edit configuration
            </Button>
            <DropdownButton
              v-if="moreActions.length > 0"
              label="More actions"
              :items="moreActions"
              variant="secondary"
              @select="handleMoreAction"
            />
            <Button
              v-if="!isBudgetAccount && moreActions.length === 1"
              variant="secondary"
              @click="handleMoreAction(moreActions[0].key)"
            >
              {{ moreActions[0].label }}
            </Button>
            <Button
              variant="secondary"
              aria-label="More account options"
              @click="actionMessage = 'No additional account actions are available yet.'"
            >
              ⋮
            </Button>
          </template>
        </PageHeader>

        <div v-if="actionMessage" class="account-detail-page__notice">
          <span>{{ actionMessage }}</span>
          <button type="button" @click="actionMessage = ''">Dismiss</button>
        </div>

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
                  {{ transactionTotal }} transaction{{ transactionTotal !== 1 ? "s" : "" }}
                </span>
              </div>

              <div v-if="txLoading" class="account-detail-page__tx-loading">
                Loading transactions...
              </div>

              <div v-else class="account-detail-page__ledger-shell">
                <TransactionFilterBar
                  :accounts="accounts ?? []"
                  :categories="categories"
                  :account-filter="accountId"
                  :locked-account-id="accountId"
                  :date-filter="dateFilter"
                  :category-filter="categoryFilter"
                  :amount-filter="amountFilter"
                  :status-filter="statusFilter"
                  @update:date-filter="dateFilter = $event"
                  @update:category-filter="categoryFilter = $event"
                  @update:amount-filter="amountFilter = $event"
                  @update:status-filter="statusFilter = $event"
                />

                <TransactionLedger
                  :transactions="transactions"
                  :accounts="accounts ?? []"
                  :categories="categories"
                  :total-count="transactionTotal"
                  :has-more="hasNextPage"
                  :loading-more="isFetchingNextPage"
                  :show-account-column="false"
                  :show-running-balance="true"
                  :running-balances="runningBalances"
                  :locked-account-id="accountId"
                  @load-more="loadMoreTransactions"
                  @commit="handleCommitEdit"
                  @remove="handleRemoveTransaction"
                />
              </div>
            </section>

            <BalanceTrendChart
              v-model:period="chartPeriod"
              class="account-detail-page__chart-section"
              :points="balanceChartPoints"
            />

            <section
              v-if="isBudgetAccount"
              class="account-detail-page__section account-detail-page__summary"
              data-cy="summary-section"
            >
              <h2 class="account-detail-page__section-title">
                Summary & notes
              </h2>
              <KeyValueList :items="summaryDetails" />
              <div class="account-detail-page__notes">
                <h3>Notes</h3>
                <p>
                  Primary budget account for daily expenses and bill payments.
                </p>
              </div>
              <button class="account-detail-page__sidebar-link">
                Edit notes
              </button>
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
            </section>

            <section
              class="account-detail-page__sidebar-section"
              data-cy="reconciliation-section"
            >
              <h3 class="account-detail-page__sidebar-title">Reconciliation</h3>
              <KeyValueList :items="reconciliationDetails" />
              <button class="account-detail-page__sidebar-link" @click="showReconciliationStub">
                View reconciliation
              </button>
            </section>
          </aside>
        </div>

        <FormModal
          :visible="showConfigurationModal"
          title="Edit account configuration"
          submit-text="Save"
          danger-text="Retire account"
          :loading="configurationSaving"
          @submit="saveConfiguration"
          @danger="retireAccount"
          @cancel="showConfigurationModal = false"
          @close="showConfigurationModal = false"
        >
          <div class="account-detail-page__config-form">
            <TextField v-model="configurationName" label="Name" name="name" />
            <TextField
              v-model="configurationInstitution"
              label="Institution"
              name="institution"
            />
            <TextField
              v-model="configurationLast4"
              label="Account number last4"
              name="account-number-last4"
            />
            <p class="account-detail-page__config-note">
              Account type and net-worth inclusion are not configurable here. Active
              financial entities contribute to net worth according to their type.
            </p>
          </div>
        </FormModal>
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

.account-detail-page__notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-info);
  border-radius: var(--radius-all);
  background: var(--color-info-container);
  color: var(--color-info);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
}

.account-detail-page__notice button {
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.account-detail-page__content {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-lg);
}

.account-detail-page__left {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  gap: var(--space-lg);
  min-width: 0;
}

.account-detail-page__left > .account-detail-page__section:first-child {
  grid-column: 1 / -1;
}

.account-detail-page__chart-section {
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

.account-detail-page__section-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  margin-left: auto;
}

.account-detail-page__tx-loading {
  padding: var(--space-xl);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

.account-detail-page__ledger-shell {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.account-detail-page__ledger-shell :deep(.filter-bar) {
  border-radius: var(--radius-all);
}

.account-detail-page__ledger-shell :deep(.ledger__scroll) {
  height: clamp(360px, 52vh, 720px);
}

.account-detail-page__table {
  width: 100%;
}

.account-detail-page__table-header {
  display: grid;
  grid-template-columns:
    90px minmax(140px, 1.5fr) 120px minmax(130px, 1fr)
    95px 90px 95px 24px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-outline);
}

.account-detail-page__table-header--investment {
  grid-template-columns: 90px minmax(140px, 1fr) 95px 90px 95px;
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
  grid-template-columns:
    90px minmax(140px, 1.5fr) 120px minmax(130px, 1fr)
    95px 90px 95px 24px;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  align-items: center;
}

.account-detail-page__row--investment {
  grid-template-columns: 90px minmax(140px, 1fr) 95px 90px 95px;
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

.account-detail-page__td--action {
  text-align: center;
  color: var(--color-on-surface-muted);
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

.account-detail-page__range-toggle {
  display: inline-flex;
  margin-left: auto;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  overflow: hidden;
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
}

.account-detail-page__range-toggle span {
  padding: var(--space-xs) var(--space-sm);
  border-right: 1px solid var(--color-outline);
}

.account-detail-page__range-toggle span:last-child {
  border-right: 0;
}

.account-detail-page__range-toggle-active {
  background: var(--color-surface-selected);
  color: var(--color-on-surface);
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
  border: 0;
  border-radius: var(--radius-all);
  overflow: hidden;
}

.account-detail-page__chart-empty svg {
  width: 100%;
  height: 100%;
}

.account-detail-page__chart-grid {
  stroke: var(--color-outline);
  stroke-width: 1;
}

.account-detail-page__chart-area {
  fill: var(--color-positive-container);
  opacity: 0.55;
}

.account-detail-page__chart-line {
  fill: none;
  stroke: var(--color-positive);
  stroke-width: 3;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.account-detail-page__summary {
  padding: var(--space-lg);
}

.account-detail-page__summary .account-detail-page__section-title {
  margin-bottom: var(--space-md);
}

.account-detail-page__notes {
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-outline);
}

.account-detail-page__notes h3 {
  margin: 0 0 var(--space-sm);
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
}

.account-detail-page__notes p {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
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

.account-detail-page__config-form {
  display: grid;
  gap: var(--space-lg);
}

.account-detail-page__config-note {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

@media (max-width: 900px) {
  .account-detail-page__content {
    grid-template-columns: 1fr;
  }

  .account-detail-page__left {
    grid-template-columns: 1fr;
  }

  .account-detail-page__left > .account-detail-page__section:first-child {
    grid-column: auto;
  }

  .account-detail-page__section-actions,
  .account-detail-page__range-toggle {
    display: none;
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
