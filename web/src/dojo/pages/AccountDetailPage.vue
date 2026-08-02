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
  createTangibleValuation,
  createTrackingSnapshot,
  createInvestmentTransfer,
  createLoanPayment,
  fetchAccountBudgetLinks,
  fetchAccounts,
  fetchAccountBalanceTrend,
  fetchAccountTransactionSummary,
  fetchCategories,
  fetchLatestInvestmentStatement,
  fetchLoanPayments,
  fetchLoanSnapshots,
  fetchTrackingSnapshots,
  fetchTangibleValuations,
  fetchTransactionsPage,
  reconcileInvestmentStatement,
  reconcileLoanStatement,
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
import CurrencyField from "@/dojo/components/forms/CurrencyField.vue";
import DatePicker from "@/dojo/components/forms/DatePicker.vue";
import SelectField from "@/dojo/components/forms/SelectField.vue";
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
const showValueModal = ref(false);
const valueDate = ref(new Date().toISOString().slice(0, 10));
const valueAmount = ref("");
const valueNotes = ref("");
const showInvestmentStatementModal = ref(false);
const investmentStatementDate = ref(new Date().toISOString().slice(0, 10));
const investmentStatementCash = ref("");
const investmentStatementNotes = ref("");
const investmentHoldingRows = ref<
  Array<{
    ticker: string;
    quantity: string;
    price: string;
    averageBasis: string;
  }>
>([]);
const showInvestmentTransferModal = ref(false);
const investmentTransferDirection = ref<"CONTRIBUTION" | "WITHDRAWAL">(
  "CONTRIBUTION",
);
const investmentTransferDate = ref(new Date().toISOString().slice(0, 10));
const investmentTransferBudgetAccountId = ref("");
const investmentTransferCategoryId = ref("");
const investmentTransferAmount = ref("");
const investmentTransferMemo = ref("");
const investmentTransferStatus = ref<"PENDING" | "CLEARED">("CLEARED");
const investmentTransferFundShortfall = ref(true);
const showLoanPaymentModal = ref(false);
const loanPaymentDate = ref(new Date().toISOString().slice(0, 10));
const loanPaymentBudgetAccountId = ref("");
const loanPaymentCategoryId = ref("");
const loanPaymentAmount = ref("");
const loanPaymentMemo = ref("Loan payment");
const showLoanStatementModal = ref(false);
const loanStatementDate = ref(new Date().toISOString().slice(0, 10));
const loanPrincipal = ref("");
const loanAccruedInterest = ref("");
const loanEscrow = ref("");
const loanUnapplied = ref("");

const { data: categoriesResponse } = useQuery({
  queryKey: computed(() => ["categories", currentMonth.value]),
  queryFn: () => fetchCategories(currentMonth.value, false),
});

const categories = computed(() => categoriesResponse.value?.items ?? []);

const transactionFilters = computed<TransactionFilters>(() => ({
  accountId: accountId.value,
  sortBy: "date",
  sortDir: "desc",
  ...(categoryFilter.value !== "all"
    ? { categoryId: categoryFilter.value }
    : {}),
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
    fetchTransactionsPage(
      false,
      pageParam,
      TRANSACTION_PAGE_SIZE,
      transactionFilters.value,
    ),
  initialPageParam: 0,
  getNextPageParam: (lastPage) =>
    lastPage.has_more ? lastPage.offset + lastPage.limit : undefined,
  enabled: computed(() => !!accountId.value),
});

const transactions = computed(
  () => txPages.value?.pages.flatMap((page) => page.items) ?? [],
);
const transactionTotal = computed(() => txPages.value?.pages[0]?.total ?? 0);
const transactionStatusCounts = computed(
  () => txPages.value?.pages[0]?.status_counts ?? { PENDING: 0, CLEARED: 0 },
);

const { data: summaryData } = useQuery({
  queryKey: computed(() => ["account-transaction-summary", accountId.value]),
  queryFn: () => fetchAccountTransactionSummary(accountId.value),
  enabled: computed(() => !!accountId.value),
});

const { data: trendData } = useQuery({
  queryKey: computed(() => [
    "account-balance-trend",
    accountId.value,
    chartPeriod.value,
  ]),
  queryFn: () => fetchAccountBalanceTrend(accountId.value, chartPeriod.value),
  enabled: computed(() => !!accountId.value),
});

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
const isValuationEntity = computed(
  () => isTrackingAccount.value || isTangibleAsset.value,
);
const accountCurrentValue = computed(() => {
  if (!account.value) return null;
  if (account.value.current_value_minor !== undefined) {
    return account.value.current_value_minor;
  }
  if (isTrackingAccount.value) {
    return account.value.latest_valuation_minor ?? null;
  }
  if (isBudgetAccount.value) {
    return account.value.display_balance_minor;
  }
  return null;
});

const { data: trackingSnapshots } = useQuery({
  queryKey: computed(() => ["tracking-snapshots", accountId.value]),
  queryFn: () => fetchTrackingSnapshots(accountId.value),
  enabled: computed(() => !!accountId.value && isTrackingAccount.value),
});

const { data: tangibleValuations } = useQuery({
  queryKey: computed(() => ["tangible-valuations", accountId.value]),
  queryFn: () => fetchTangibleValuations(accountId.value),
  enabled: computed(() => !!accountId.value && isTangibleAsset.value),
});

const { data: investmentStatement } = useQuery({
  queryKey: computed(() => ["investment-statement", accountId.value]),
  queryFn: () => fetchLatestInvestmentStatement(accountId.value),
  enabled: computed(() => !!accountId.value && isInvestmentAccount.value),
});

const { data: accountBudgetLinks } = useQuery({
  queryKey: computed(() => ["account-budget-links", accountId.value]),
  queryFn: () => fetchAccountBudgetLinks(accountId.value),
  enabled: computed(
    () =>
      !!accountId.value && (isInvestmentAccount.value || isLoanAccount.value),
  ),
});
const { data: loanSnapshots } = useQuery({
  queryKey: computed(() => ["loan-snapshots", accountId.value]),
  queryFn: () => fetchLoanSnapshots(accountId.value),
  enabled: computed(() => !!accountId.value && isLoanAccount.value),
});
const { data: loanPayments } = useQuery({
  queryKey: computed(() => ["loan-payments", accountId.value]),
  queryFn: () => fetchLoanPayments(accountId.value),
  enabled: computed(() => !!accountId.value && isLoanAccount.value),
});
const latestLoanSnapshot = computed(() => loanSnapshots.value?.[0]);

const budgetAccountOptions = computed(() =>
  (accounts.value ?? [])
    .filter(
      (candidate) =>
        candidate.account_class === "BUDGET" &&
        candidate.budget_account_type !== "CREDIT_CARD",
    )
    .map((candidate) => ({
      value: candidate.account_id,
      label: candidate.name,
    })),
);
const contributionCategoryOptions = computed(() =>
  categories.value
    .filter((category) => category.category_kind === "STANDARD")
    .map((category) => ({ value: category.category_id, label: category.name })),
);
const linkedContributionCategoryId = computed(
  () =>
    accountBudgetLinks.value?.find(
      (link) => link.link_behavior === "INVESTMENT_CONTRIBUTION",
    )?.category_id ?? "",
);
const linkedLoanCategoryId = computed(
  () =>
    accountBudgetLinks.value?.find(
      (link) => link.link_behavior === "LOAN_PAYMENT",
    )?.category_id ?? "",
);
const selectedContributionCategory = computed(() =>
  categories.value.find(
    (category) => category.category_id === investmentTransferCategoryId.value,
  ),
);

const valueHistory = computed(() =>
  isTrackingAccount.value
    ? (trackingSnapshots.value ?? [])
    : (tangibleValuations.value ?? []),
);

const showCutoverModal = ref(false);
const cutoverEntityType = ref("INVESTMENT");
const cutoverDate = ref(new Date().toISOString().slice(0, 10));
const cutoverName = ref("");
const cutoverOpeningValue = ref("");
const cutoverContributionCategory = ref("create");
const cutoverRepresentationConfirmed = ref(true);

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
        value: "Not reconciled",
        auxValue: "No reconciliation recorded",
        status: { label: "", variant: "warning" as const },
      },
    ];
  }

  if (isInvestmentAccount.value) {
    const currentValue = accountCurrentValue.value;
    const change = account.value.change_30d_minor;
    return [
      {
        key: "value",
        label: "Current value",
        value: formatOptionalCurrency(currentValue),
        auxValue: valueAsOfLabel.value,
      },
      {
        key: "cash",
        label: "Cash",
        value: formatOptionalCurrency(
          investmentStatement.value?.cash_balance_minor,
        ),
        auxValue: valueAsOfLabel.value,
      },
      {
        key: "holdings",
        label: "Holdings value",
        value: formatOptionalCurrency(
          investmentStatement.value?.holdings_value_minor,
        ),
        auxValue: valueAsOfLabel.value,
      },
      {
        key: "change",
        label: "30d change",
        value:
          change === null || change === undefined
            ? "—"
            : formatCurrency(change),
        auxValue:
          change === null || change === undefined ? "Unavailable" : "30 days",
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.net_worth_contribution_minor ?? 0),
        auxValue: "Asset",
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Not reconciled",
        auxValue: "No statement recorded",
        status: { label: "", variant: "warning" as const },
      },
    ];
  }

  if (isLoanAccount.value) {
    const obligation = accountCurrentValue.value;
    return [
      {
        key: "obligation",
        label: "Current obligation",
        value: formatOptionalCurrency(obligation),
        auxValue: valueAsOfLabel.value,
      },
      {
        key: "balance",
        label: "Principal balance",
        value: formatOptionalCurrency(obligation),
        auxValue: valueAsOfLabel.value,
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.net_worth_contribution_minor ?? 0),
        auxValue: "Liability",
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Not reconciled",
        auxValue: "No statement recorded",
        status: { label: "", variant: "warning" as const },
      },
    ];
  }

  if (isTrackingAccount.value) {
    const valuationDate = account.value.latest_valuation_date
      ? formatDateShort(
          new Date(account.value.latest_valuation_date + "T00:00:00"),
        )
      : formatDateShort();
    const polarityLabel =
      account.value.tracking_polarity === "LIABILITY" ? "Liability" : "Asset";
    const polarityArrow =
      account.value.tracking_polarity === "LIABILITY" ? "" : " \u2191";
    const polarityVariant =
      account.value.tracking_polarity === "LIABILITY" ? "error" : "positive";
    const sourceLabel =
      account.value.tracking_source === "import" ? "Aspire" : "Manual";
    const sourceSub =
      account.value.tracking_source === "import"
        ? "Net-worth migration"
        : "User entry";
    const latestSnapshotDate = account.value.latest_valuation_date
      ? formatDateShort(
          new Date(account.value.latest_valuation_date + "T00:00:00"),
        )
      : "No snapshots";
    return [
      {
        key: "value",
        label: "Current value",
        value: formatOptionalCurrency(accountCurrentValue.value),
        auxValue: `As of ${valuationDate}`,
      },
      {
        key: "polarity",
        label: "Polarity",
        value: `${polarityLabel}${polarityArrow}`,
        auxValue: "Positive",
        status: { label: "", variant: polarityVariant as "positive" | "error" },
      },
      {
        key: "snapshot",
        label: "Latest snapshot",
        value: latestSnapshotDate,
        auxValue: "Daily",
      },
      {
        key: "source",
        label: "Source / migration",
        value: sourceLabel,
        auxValue: sourceSub,
      },
      {
        key: "recon",
        label: "Reconciliation freshness",
        value: "Not reconciled",
        auxValue: "No reconciliation recorded",
        status: { label: "", variant: "warning" as const },
      },
    ];
  }

  return [
    {
      key: "value",
      label: "Current value",
      value: formatOptionalCurrency(accountCurrentValue.value),
      auxValue: valueAsOfLabel.value,
    },
    {
      key: "net-worth",
      label: "Net worth contribution",
      value: formatCurrency(account.value.net_worth_contribution_minor ?? 0),
      auxValue: isTrackingAccount.value ? "Asset" : "Assets",
    },
    {
      key: "recon",
      label: "Reconciliation freshness",
      value: "Not reconciled",
      auxValue: "No reconciliation recorded",
      status: { label: "", variant: "warning" as const },
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
  if (isInvestmentAccount.value) {
    items.push({
      label: "Investment style",
      value: account.value.investment_self_managed ? "Self-managed" : "Managed",
    });
    items.push({
      label: "Tax treatment",
      value: formatTaxTreatment(account.value.investment_tax_treatment),
    });
  }
  items.push({
    label: "Current balance",
    value: isBudgetAccount.value
      ? formatCurrency(account.value.display_balance_minor)
      : formatOptionalCurrency(accountCurrentValue.value),
  });
  return items;
});

const reconciliationDetails = computed((): KeyValueItem[] => [
  { label: "Status", value: "Not reconciled", variant: "warning" },
  { label: "Last reconciled", value: "—" },
  { label: "Statement balance", value: "—" },
  { label: "Difference", value: "—" },
]);

const summaryDetails = computed((): KeyValueItem[] => {
  const summary = summaryData.value;
  const inflow = summary?.inflow_minor ?? 0;
  const outflow = summary?.outflow_minor ?? 0;
  const netFlow = summary?.net_flow_minor ?? 0;
  const averageDailyBalance = summary?.average_daily_balance_minor ?? 0;

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

const trackingSummaryDetails = computed((): KeyValueItem[] => {
  const summary = summaryData.value;
  const inflow = summary?.inflow_minor ?? 0;
  const outflow = summary?.outflow_minor ?? 0;
  const netFlow = summary?.net_flow_minor ?? 0;
  const averageDailyBalance = summary?.average_daily_balance_minor ?? 0;

  return [
    { label: "30d inflow", value: formatCurrency(inflow) },
    { label: "30d outflow", value: formatCurrency(outflow), variant: "error" },
    {
      label: "30d net flow",
      value: formatCurrency(netFlow),
      variant: netFlow >= 0 ? "positive" : "error",
    },
    {
      label: "Average daily value",
      value: formatCurrency(averageDailyBalance),
    },
  ];
});

const migrationContextDetails = computed((): KeyValueItem[] => [
  { label: "Imported from", value: "Google Aspire" },
  { label: "Imported on", value: "—" },
  { label: "Import type", value: "Net-worth migration" },
]);

const historyConfigDetails = computed((): KeyValueItem[] => {
  const items: KeyValueItem[] = [];
  items.push({
    label: "Created",
    value: account.value?.created_at
      ? formatDateShort(new Date(account.value.created_at))
      : "—",
  });
  const latestDate = account.value?.latest_valuation_date;
  if (latestDate) {
    items.push({
      label: "Last snapshot",
      value: formatDateShort(new Date(latestDate + "T00:00:00")),
    });
  }
  items.push({ label: "Configuration", value: "" });
  return items;
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

const valueAsOfLabel = computed(() => {
  const effectiveDate = account.value?.value_effective_date;
  if (!effectiveDate) return "No value recorded";
  return `As of ${formatDateShort(new Date(`${effectiveDate}T00:00:00`))}`;
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

const balanceChartPoints = computed(() =>
  (trendData.value?.points ?? []).map((point) => ({
    date: point.date,
    valueMinor: point.balance_minor,
  })),
);

const moreActions = computed(() => {
  const actions: { key: string; label: string }[] = [];
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
  mutationFn: ({
    id,
    payload,
  }: {
    id: string;
    payload: Record<string, unknown>;
  }) => updateAccount(id, payload),
  onSuccess: () => {
    showConfigurationModal.value = false;
    invalidateAccountDetailQueries();
  },
});
const createValueMutation = useMutation({
  mutationFn: (payload: {
    effective_date: string;
    amount_minor: number;
    source: string;
    notes: string;
  }) =>
    isTrackingAccount.value
      ? createTrackingSnapshot(accountId.value, payload)
      : createTangibleValuation(accountId.value, payload),
  onSuccess: () => {
    showValueModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["tracking-snapshots"] });
    queryClient.invalidateQueries({ queryKey: ["tangible-valuations"] });
    invalidateAccountDetailQueries();
  },
});
const reconcileInvestmentMutation = useMutation({
  mutationFn: (payload: Parameters<typeof reconcileInvestmentStatement>[1]) =>
    reconcileInvestmentStatement(accountId.value, payload),
  onSuccess: () => {
    showInvestmentStatementModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["investment-statement"] });
    invalidateAccountDetailQueries();
  },
});
const investmentTransferMutation = useMutation({
  mutationFn: (payload: Parameters<typeof createInvestmentTransfer>[1]) =>
    createInvestmentTransfer(accountId.value, payload),
  onSuccess: () => {
    showInvestmentTransferModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["account-budget-links"] });
    invalidateAccountDetailQueries();
  },
});
const loanPaymentMutation = useMutation({
  mutationFn: (payload: Parameters<typeof createLoanPayment>[1]) =>
    createLoanPayment(accountId.value, payload),
  onSuccess: () => {
    showLoanPaymentModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["loan-payments"] });
    queryClient.invalidateQueries({ queryKey: ["account-budget-links"] });
    invalidateAccountDetailQueries();
  },
});
const loanStatementMutation = useMutation({
  mutationFn: (payload: Parameters<typeof reconcileLoanStatement>[1]) =>
    reconcileLoanStatement(accountId.value, payload),
  onSuccess: () => {
    showLoanStatementModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["loan-snapshots"] });
    invalidateAccountDetailQueries();
  },
});
const configurationSaving = computed(
  () => updateAccountMutation.isPending.value,
);

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
  queryClient.invalidateQueries({ queryKey: ["account-transaction-summary"] });
  queryClient.invalidateQueries({ queryKey: ["account-balance-trend"] });
  queryClient.invalidateQueries({ queryKey: ["assets-liabilities"] });
  queryClient.invalidateQueries({ queryKey: ["budget"] });
  queryClient.invalidateQueries({ queryKey: ["allocations"] });
  queryClient.invalidateQueries({ queryKey: ["net-worth"] });
}

function openValueModal() {
  valueDate.value = new Date().toISOString().slice(0, 10);
  valueAmount.value = "";
  valueNotes.value = "";
  showValueModal.value = true;
}

function saveValue() {
  const amountMinor = parseCurrencyMinor(valueAmount.value);
  if (amountMinor === null) return;
  createValueMutation.mutate({
    effective_date: valueDate.value,
    amount_minor: amountMinor,
    source: "manual",
    notes: valueNotes.value,
  });
}

function openInvestmentStatementModal() {
  const statement = investmentStatement.value;
  investmentStatementDate.value =
    statement?.effective_date ?? new Date().toISOString().slice(0, 10);
  investmentStatementCash.value =
    statement?.cash_balance_minor === null ||
    statement?.cash_balance_minor === undefined
      ? ""
      : String(statement.cash_balance_minor / 100);
  investmentStatementNotes.value = "";
  investmentHoldingRows.value = (statement?.holdings ?? []).map((holding) => ({
    ticker: holding.ticker,
    quantity: String(holding.quantity_micros / 1_000_000),
    price: String(holding.price_minor / 100),
    averageBasis:
      holding.average_basis_minor === null
        ? ""
        : String(holding.average_basis_minor / 100),
  }));
  if (investmentHoldingRows.value.length === 0) addInvestmentHoldingRow();
  showInvestmentStatementModal.value = true;
}

function addInvestmentHoldingRow() {
  investmentHoldingRows.value.push({
    ticker: "",
    quantity: "",
    price: "",
    averageBasis: "",
  });
}

function removeInvestmentHoldingRow(index: number) {
  investmentHoldingRows.value.splice(index, 1);
}

function saveInvestmentStatement() {
  const cash = parseCurrencyMinor(investmentStatementCash.value);
  if (cash === null) return;
  const holdings = investmentHoldingRows.value.map((holding) => ({
    ticker: holding.ticker.trim().toUpperCase(),
    quantity_micros: Math.round(Number(holding.quantity) * 1_000_000),
    price_minor: parseCurrencyMinor(holding.price) ?? 0,
    ...(holding.averageBasis.trim()
      ? { average_basis_minor: parseCurrencyMinor(holding.averageBasis) ?? 0 }
      : {}),
  }));
  reconcileInvestmentMutation.mutate({
    effective_date: investmentStatementDate.value,
    cash_balance_minor: cash,
    holdings,
    notes: investmentStatementNotes.value,
  });
}

function openInvestmentTransferModal(direction: "CONTRIBUTION" | "WITHDRAWAL") {
  investmentTransferDirection.value = direction;
  investmentTransferDate.value = new Date().toISOString().slice(0, 10);
  investmentTransferBudgetAccountId.value =
    budgetAccountOptions.value[0]?.value ?? "";
  investmentTransferCategoryId.value =
    linkedContributionCategoryId.value ??
    contributionCategoryOptions.value[0]?.value ??
    "";
  if (!investmentTransferCategoryId.value) {
    investmentTransferCategoryId.value =
      contributionCategoryOptions.value[0]?.value ?? "";
  }
  investmentTransferAmount.value = "";
  investmentTransferMemo.value =
    direction === "CONTRIBUTION"
      ? "Investment contribution"
      : "Investment withdrawal";
  investmentTransferStatus.value = "CLEARED";
  investmentTransferFundShortfall.value = true;
  showInvestmentTransferModal.value = true;
}

function saveInvestmentTransfer() {
  const amount = parseCurrencyMinor(investmentTransferAmount.value);
  if (amount === null || !investmentTransferBudgetAccountId.value) return;
  investmentTransferMutation.mutate({
    direction: investmentTransferDirection.value,
    budget_account_id: investmentTransferBudgetAccountId.value,
    date: investmentTransferDate.value,
    amount_minor: amount,
    status: investmentTransferStatus.value,
    memo: investmentTransferMemo.value,
    fund_shortfall: investmentTransferFundShortfall.value,
    ...(investmentTransferDirection.value === "CONTRIBUTION" &&
    investmentTransferCategoryId.value
      ? { contribution_category_id: investmentTransferCategoryId.value }
      : {}),
  });
}

const investmentTransferCanSave = computed(
  () =>
    parseCurrencyMinor(investmentTransferAmount.value) !== null &&
    investmentTransferBudgetAccountId.value.length > 0 &&
    (investmentTransferDirection.value === "WITHDRAWAL" ||
      investmentTransferCategoryId.value.length > 0),
);

function openLoanPaymentModal() {
  loanPaymentDate.value = new Date().toISOString().slice(0, 10);
  loanPaymentBudgetAccountId.value = budgetAccountOptions.value[0]?.value ?? "";
  loanPaymentCategoryId.value =
    linkedLoanCategoryId.value ||
    contributionCategoryOptions.value[0]?.value ||
    "";
  loanPaymentAmount.value = "";
  loanPaymentMemo.value = "Loan payment";
  showLoanPaymentModal.value = true;
}

function saveLoanPayment() {
  const amount = parseCurrencyMinor(loanPaymentAmount.value);
  if (amount === null) return;
  loanPaymentMutation.mutate({
    date: loanPaymentDate.value,
    budget_account_id: loanPaymentBudgetAccountId.value,
    amount_minor: amount,
    category_id: loanPaymentCategoryId.value,
    status: "CLEARED",
    memo: loanPaymentMemo.value,
  });
}

function openLoanStatementModal() {
  const snapshot = latestLoanSnapshot.value;
  loanStatementDate.value = new Date().toISOString().slice(0, 10);
  loanPrincipal.value = snapshot
    ? String(snapshot.principal_balance_minor / 100)
    : "";
  loanAccruedInterest.value = snapshot?.accrued_interest_minor
    ? String(snapshot.accrued_interest_minor / 100)
    : "0";
  loanEscrow.value = snapshot
    ? String(snapshot.escrow_balance_minor / 100)
    : "0";
  loanUnapplied.value = snapshot
    ? String(snapshot.unapplied_credit_minor / 100)
    : "0";
  showLoanStatementModal.value = true;
}

function saveLoanStatement() {
  const principal = parseCurrencyMinor(loanPrincipal.value);
  if (principal === null) return;
  loanStatementMutation.mutate({
    effective_date: loanStatementDate.value,
    principal_balance_minor: principal,
    accrued_interest_minor: parseCurrencyMinor(loanAccruedInterest.value) ?? 0,
    escrow_balance_minor: parseCurrencyMinor(loanEscrow.value) ?? 0,
    unapplied_credit_minor: parseCurrencyMinor(loanUnapplied.value) ?? 0,
  });
}

const investmentStatementCanSave = computed(() => {
  if (parseCurrencyMinor(investmentStatementCash.value) === null) return false;
  return investmentHoldingRows.value.every(
    (holding) =>
      holding.ticker.trim().length > 0 &&
      Number.isFinite(Number(holding.quantity)) &&
      Number(holding.quantity) >= 0 &&
      (parseCurrencyMinor(holding.price) ?? 0) > 0,
  );
});

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
  configurationName.value =
    cleanAccountName(account.value.name) ?? account.value.name;
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

function openCutoverModal() {
  if (!account.value) return;
  const latestValuation = account.value.display_balance_minor;
  cutoverName.value = cleanAccountName(account.value.name)
    ? `${cleanAccountName(account.value.name)} (Upgraded)`
    : `${account.value.name} (Upgraded)`;
  cutoverOpeningValue.value = String(latestValuation);
  cutoverDate.value = new Date().toISOString().slice(0, 10);
  cutoverEntityType.value = "INVESTMENT";
  cutoverContributionCategory.value = "create";
  cutoverRepresentationConfirmed.value = true;
  showCutoverModal.value = true;
}

function handleCutoverSubmit() {
  showCutoverModal.value = false;
  actionMessage.value =
    "Account cutover is a representation change, not a ledger transfer. This flow will persist the cutover when the backend endpoint is available.";
}

function datePresetToFilter(
  value: string,
): Pick<TransactionFilters, "dateFrom" | "dateTo"> {
  const today = new Date();
  const toIso = (date: Date) => date.toISOString().slice(0, 10);
  if (value === "today")
    return { dateFrom: toIso(today), dateTo: toIso(today) };
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
  if (value === "50-100")
    return { amountMinMinor: 5_000, amountMaxMinor: 10_000 };
  if (value === "100-500")
    return { amountMinMinor: 10_000, amountMaxMinor: 50_000 };
  if (value === "500+") return { amountMinMinor: 50_000 };
  return {};
}

function parseCurrencyMinor(value: string): number | null {
  const amount = Number(value.replace(/[$,]/g, "").trim());
  if (!Number.isFinite(amount) || amount < 0) return null;
  return Math.round(amount * 100);
}

function cleanAccountName(name: string | undefined): string | null {
  if (!name) return null;
  return name.replace(/^[^\p{L}\p{N}]+\s*/u, "").trim() || name;
}

function formatDateShort(date?: Date): string {
  return (date ?? new Date()).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatOptionalCurrency(
  amountMinor: number | null | undefined,
): string {
  return amountMinor === null || amountMinor === undefined
    ? "—"
    : formatCurrency(amountMinor);
}

function formatTaxTreatment(value: string | null | undefined): string {
  if (!value) return "—";
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
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
              v-if="isValuationEntity"
              data-cy="account-detail-add-snapshot"
              @click="openValueModal"
            >
              {{ isTrackingAccount ? "Add snapshot" : "Add valuation" }}
            </Button>
            <Button
              v-if="isTrackingAccount"
              variant="secondary"
              data-cy="account-detail-create-richer"
              @click="openCutoverModal"
            >
              Create richer account
            </Button>
            <Button
              v-if="isLoanAccount"
              data-cy="account-detail-record-payment"
              @click="openLoanPaymentModal"
            >
              Record payment
            </Button>
            <Button
              v-if="isLoanAccount"
              variant="secondary"
              data-cy="account-detail-reconcile-loan"
              @click="openLoanStatementModal"
            >
              Reconcile statement
            </Button>
            <Button
              v-if="isInvestmentAccount"
              data-cy="account-detail-contribute"
              @click="openInvestmentTransferModal('CONTRIBUTION')"
            >
              Contribute
            </Button>
            <Button
              v-if="isInvestmentAccount"
              variant="secondary"
              data-cy="account-detail-withdraw"
              @click="openInvestmentTransferModal('WITHDRAWAL')"
            >
              Withdraw
            </Button>
            <Button
              v-if="isInvestmentAccount"
              variant="secondary"
              data-cy="account-detail-reconcile-investment"
              @click="openInvestmentStatementModal"
            >
              Reconcile statement
            </Button>
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
              @click="
                actionMessage =
                  'No additional account actions are available yet.'
              "
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

        <div
          v-if="isTrackingAccount && account?.tracking_source === 'import'"
          class="account-detail-page__info-banner"
          data-cy="tracking-import-banner"
        >
          <svg
            class="account-detail-page__info-icon"
            viewBox="0 0 16 16"
            fill="none"
          >
            <circle
              cx="8"
              cy="8"
              r="7"
              stroke="currentColor"
              stroke-width="1.5"
            />
            <path
              d="M8 5v0m0 3v4"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
          This tracking account was imported from Google Aspire during net-worth
          migration.
        </div>

        <div class="account-detail-page__content">
          <div class="account-detail-page__left">
            <template v-if="isValuationEntity">
              <section
                class="account-detail-page__section"
                data-cy="snapshot-history-section"
              >
                <div class="account-detail-page__section-header">
                  <svg
                    class="account-detail-page__section-icon"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <circle
                      cx="8"
                      cy="8"
                      r="6"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path
                      d="M8 5v3l2 1"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <h2 class="account-detail-page__section-title">
                    {{
                      isTrackingAccount
                        ? "Snapshot history"
                        : "Valuation history"
                    }}
                  </h2>
                  <span class="account-detail-page__section-count">
                    {{ valueHistory.length }}
                    {{ isTrackingAccount ? "snapshot" : "valuation"
                    }}{{ valueHistory.length !== 1 ? "s" : "" }}
                  </span>
                </div>
                <div class="account-detail-page__snapshot-table">
                  <div class="account-detail-page__snapshot-header">
                    <span class="account-detail-page__snapshot-th">Date ↓</span>
                    <span
                      class="account-detail-page__snapshot-th account-detail-page__snapshot-th--end"
                      >Value</span
                    >
                  </div>
                  <div
                    v-for="snapshot in valueHistory"
                    :key="snapshot.valuation_id"
                    class="account-detail-page__snapshot-row"
                  >
                    <span class="account-detail-page__snapshot-td">
                      <span class="account-detail-page__snapshot-dot" />
                      {{
                        formatDateShort(
                          new Date(snapshot.effective_date + "T00:00:00"),
                        )
                      }}
                    </span>
                    <span
                      class="account-detail-page__snapshot-td account-detail-page__snapshot-td--end"
                    >
                      {{ formatCurrency(snapshot.amount_minor) }}
                    </span>
                  </div>
                </div>
              </section>

              <BalanceTrendChart
                v-model:period="chartPeriod"
                class="account-detail-page__chart-section"
                :points="balanceChartPoints"
              />

              <section
                class="account-detail-page__section account-detail-page__summary"
                data-cy="tracking-summary-section"
              >
                <h2 class="account-detail-page__section-title">
                  {{
                    isTrackingAccount
                      ? "Valuation history"
                      : "Valuation summary"
                  }}
                </h2>
                <p class="account-detail-page__summary-sub">
                  As of {{ formatDateShort() }}
                </p>
                <div class="account-detail-page__chart-value">
                  {{ formatOptionalCurrency(accountCurrentValue) }}
                </div>
                <p class="account-detail-page__chart-sub">Current value</p>
                <KeyValueList :items="trackingSummaryDetails" />
                <div class="account-detail-page__notes">
                  <h3>Notes</h3>
                  <p>No notes yet.</p>
                </div>
              </section>
            </template>

            <template v-else-if="isLoanAccount">
              <section
                class="account-detail-page__section"
                data-cy="loan-payments-section"
              >
                <div class="account-detail-page__section-header">
                  <h2 class="account-detail-page__section-title">
                    Payment activity
                  </h2>
                  <span class="account-detail-page__section-count">
                    {{ loanPayments?.length ?? 0 }} payments
                  </span>
                </div>
                <div class="account-detail-page__snapshot-table">
                  <div class="account-detail-page__snapshot-header">
                    <span class="account-detail-page__snapshot-th"
                      >Date / account</span
                    >
                    <span
                      class="account-detail-page__snapshot-th account-detail-page__snapshot-th--end"
                      >Amount</span
                    >
                  </div>
                  <div
                    v-for="payment in loanPayments ?? []"
                    :key="payment.transaction_id"
                    class="account-detail-page__snapshot-row"
                  >
                    <span class="account-detail-page__snapshot-td"
                      >{{ payment.date }} · {{ payment.account_name }}</span
                    >
                    <span
                      class="account-detail-page__snapshot-td account-detail-page__snapshot-td--end"
                      >{{
                        formatCurrency(Math.abs(payment.amount_minor))
                      }}</span
                    >
                  </div>
                </div>
              </section>
              <section
                class="account-detail-page__section account-detail-page__summary"
                data-cy="loan-summary-section"
              >
                <h2 class="account-detail-page__section-title">
                  Loan statement summary
                </h2>
                <KeyValueList
                  :items="[
                    {
                      label: 'Principal reduction',
                      value: formatCurrency(
                        latestLoanSnapshot?.principal_reduction_minor ?? 0,
                      ),
                    },
                    {
                      label: 'Unknown non-principal',
                      value: formatCurrency(
                        latestLoanSnapshot?.unknown_nonprincipal_minor ?? 0,
                      ),
                    },
                    {
                      label: 'Escrow balance',
                      value: formatCurrency(
                        latestLoanSnapshot?.escrow_balance_minor ?? 0,
                      ),
                    },
                    {
                      label: 'Unapplied credit',
                      value: formatCurrency(
                        latestLoanSnapshot?.unapplied_credit_minor ?? 0,
                      ),
                    },
                  ]"
                />
              </section>
            </template>

            <template v-else>
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
                    {{ transactionTotal }} transaction{{
                      transactionTotal !== 1 ? "s" : ""
                    }}
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
              <section
                v-if="isInvestmentAccount"
                class="account-detail-page__section account-detail-page__summary"
                data-cy="holdings-summary-section"
              >
                <h2 class="account-detail-page__section-title">
                  Holdings summary
                </h2>
                <p class="account-detail-page__summary-sub">
                  {{ valueAsOfLabel }}
                </p>
                <div
                  v-if="investmentStatement?.holdings.length"
                  class="account-detail-page__snapshot-table"
                >
                  <div class="account-detail-page__snapshot-header">
                    <span class="account-detail-page__snapshot-th">Symbol</span>
                    <span
                      class="account-detail-page__snapshot-th account-detail-page__snapshot-th--end"
                      >Value</span
                    >
                  </div>
                  <div
                    v-for="holding in investmentStatement.holdings"
                    :key="holding.position_id"
                    class="account-detail-page__snapshot-row"
                  >
                    <span class="account-detail-page__snapshot-td">{{
                      holding.ticker
                    }}</span>
                    <span
                      class="account-detail-page__snapshot-td account-detail-page__snapshot-td--end"
                    >
                      {{ formatCurrency(holding.value_minor) }}
                    </span>
                  </div>
                </div>
                <p v-else class="account-detail-page__empty">
                  No statement recorded.
                </p>
              </section>
            </template>
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
              v-if="isTrackingAccount && account?.tracking_source === 'import'"
              class="account-detail-page__sidebar-section"
              data-cy="migration-context-section"
            >
              <h3 class="account-detail-page__sidebar-title">
                Migration / import context
              </h3>
              <KeyValueList :items="migrationContextDetails" />
            </section>

            <section
              class="account-detail-page__sidebar-section"
              data-cy="history-config-section"
            >
              <h3 class="account-detail-page__sidebar-title">
                History / configuration
              </h3>
              <KeyValueList :items="historyConfigDetails" />
            </section>

            <section
              v-if="!isTrackingAccount"
              class="account-detail-page__sidebar-section"
              data-cy="reconciliation-section"
            >
              <h3 class="account-detail-page__sidebar-title">Reconciliation</h3>
              <KeyValueList :items="reconciliationDetails" />
              <button
                class="account-detail-page__sidebar-link"
                @click="showReconciliationStub"
              >
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
              Account type and net-worth inclusion are not configurable here.
              Active financial entities contribute to net worth according to
              their type.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showLoanPaymentModal"
          title="Record payment"
          submit-text="Record payment"
          :submit-disabled="
            parseCurrencyMinor(loanPaymentAmount) === null ||
            !loanPaymentBudgetAccountId ||
            !loanPaymentCategoryId
          "
          :loading="loanPaymentMutation.isPending.value"
          @submit="saveLoanPayment"
          @cancel="showLoanPaymentModal = false"
          @close="showLoanPaymentModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="loanPaymentDate"
              label="Date"
              name="loan-payment-date"
            />
            <SelectField
              v-model="loanPaymentBudgetAccountId"
              label="Cash account"
              name="loan-payment-account"
              :options="budgetAccountOptions"
            />
            <CurrencyField
              v-model="loanPaymentAmount"
              label="Amount"
              name="loan-payment-amount"
            />
            <SelectField
              v-model="loanPaymentCategoryId"
              label="Payment category"
              name="loan-payment-category"
              :options="contributionCategoryOptions"
            />
            <TextField
              v-model="loanPaymentMemo"
              label="Memo"
              name="loan-payment-memo"
            />
            <p class="account-detail-page__config-note">
              Enter the cash payment only. Principal and non-principal amounts
              are derived when the lender statement is reconciled.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showLoanStatementModal"
          title="Reconcile loan statement"
          submit-text="Apply statement"
          :submit-disabled="parseCurrencyMinor(loanPrincipal) === null"
          :loading="loanStatementMutation.isPending.value"
          @submit="saveLoanStatement"
          @cancel="showLoanStatementModal = false"
          @close="showLoanStatementModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="loanStatementDate"
              label="Statement date"
              name="loan-statement-date"
            />
            <CurrencyField
              v-model="loanPrincipal"
              label="Principal balance"
              name="loan-principal"
            />
            <CurrencyField
              v-model="loanAccruedInterest"
              label="Accrued interest"
              name="loan-interest"
            />
            <CurrencyField
              v-model="loanEscrow"
              label="Escrow balance"
              name="loan-escrow"
            />
            <CurrencyField
              v-model="loanUnapplied"
              label="Unapplied credit"
              name="loan-unapplied"
            />
            <p class="account-detail-page__config-note">
              dojo derives aggregate principal reduction and leaves the
              remaining attributed cash explicitly unknown non-principal.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showInvestmentTransferModal"
          :title="
            investmentTransferDirection === 'CONTRIBUTION'
              ? 'Contribute to investment account'
              : 'Withdraw from investment account'
          "
          :submit-text="
            investmentTransferDirection === 'CONTRIBUTION'
              ? 'Save contribution'
              : 'Save withdrawal'
          "
          :submit-disabled="!investmentTransferCanSave"
          :loading="investmentTransferMutation.isPending.value"
          @submit="saveInvestmentTransfer"
          @cancel="showInvestmentTransferModal = false"
          @close="showInvestmentTransferModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="investmentTransferDate"
              label="Date"
              name="investment-transfer-date"
            />
            <SelectField
              v-model="investmentTransferBudgetAccountId"
              :label="
                investmentTransferDirection === 'CONTRIBUTION'
                  ? 'From account'
                  : 'To account'
              "
              name="investment-transfer-budget-account"
              :options="budgetAccountOptions"
            />
            <CurrencyField
              v-model="investmentTransferAmount"
              label="Amount"
              name="investment-transfer-amount"
            />
            <SelectField
              v-model="investmentTransferStatus"
              label="Status"
              name="investment-transfer-status"
              :options="[
                { value: 'CLEARED', label: 'Cleared' },
                { value: 'PENDING', label: 'Pending' },
              ]"
            />
            <SelectField
              v-if="investmentTransferDirection === 'CONTRIBUTION'"
              v-model="investmentTransferCategoryId"
              label="Linked contribution category"
              name="investment-transfer-category"
              :options="contributionCategoryOptions"
            />
            <label
              v-if="investmentTransferDirection === 'CONTRIBUTION'"
              class="account-detail-page__cutover-checkbox"
            >
              <input
                v-model="investmentTransferFundShortfall"
                type="checkbox"
              />
              <span>
                Fund any category shortfall from Available to budget before the
                contribution.
              </span>
            </label>
            <TextField
              v-model="investmentTransferMemo"
              label="Memo"
              name="investment-transfer-memo"
            />
            <div class="account-detail-page__cutover-info">
              <span v-if="investmentTransferDirection === 'CONTRIBUTION'">
                Category available before contribution:
                {{
                  formatCurrency(
                    selectedContributionCategory?.available_minor ?? 0,
                  )
                }}. The transfer creates two ledger legs and does not change net
                worth or economic spending.
              </span>
              <span v-else>
                Returned cash increases Available to budget. It is not income or
                investment performance.
              </span>
            </div>
          </div>
        </FormModal>

        <FormModal
          :visible="showInvestmentStatementModal"
          title="Reconcile investment statement"
          submit-text="Apply statement"
          :submit-disabled="!investmentStatementCanSave"
          :loading="reconcileInvestmentMutation.isPending.value"
          @submit="saveInvestmentStatement"
          @cancel="showInvestmentStatementModal = false"
          @close="showInvestmentStatementModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="investmentStatementDate"
              label="Statement date"
              name="investment-statement-date"
            />
            <CurrencyField
              v-model="investmentStatementCash"
              label="Cash balance"
              name="investment-statement-cash"
            />
            <div class="account-detail-page__statement-holdings">
              <div class="account-detail-page__section-header">
                <h3 class="account-detail-page__section-title">Holdings</h3>
                <Button
                  variant="secondary"
                  size="sm"
                  @click="addInvestmentHoldingRow"
                >
                  Add holding
                </Button>
              </div>
              <div
                v-for="(holding, index) in investmentHoldingRows"
                :key="index"
                class="account-detail-page__statement-holding"
              >
                <TextField
                  v-model="holding.ticker"
                  label="Ticker"
                  :name="`holding-ticker-${index}`"
                />
                <TextField
                  v-model="holding.quantity"
                  label="Quantity"
                  :name="`holding-quantity-${index}`"
                  inputmode="decimal"
                />
                <CurrencyField
                  v-model="holding.price"
                  label="Statement price"
                  :name="`holding-price-${index}`"
                />
                <CurrencyField
                  v-model="holding.averageBasis"
                  label="Average basis"
                  :name="`holding-basis-${index}`"
                />
                <Button
                  v-if="investmentHoldingRows.length > 1"
                  variant="tertiary"
                  size="sm"
                  @click="removeInvestmentHoldingRow(index)"
                >
                  Remove
                </Button>
              </div>
            </div>
            <TextField
              v-model="investmentStatementNotes"
              label="Notes"
              name="investment-statement-notes"
            />
            <p class="account-detail-page__config-note">
              This statement replaces provisional transfer adjustments through
              the statement date. Trades, dividends, and interest are reflected
              by the holdings and cash snapshot.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showValueModal"
          :title="isTrackingAccount ? 'Add snapshot' : 'Add valuation'"
          submit-text="Save"
          :submit-disabled="parseCurrencyMinor(valueAmount) === null"
          :loading="createValueMutation.isPending.value"
          @submit="saveValue"
          @cancel="showValueModal = false"
          @close="showValueModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="valueDate"
              label="Effective date"
              name="value-date"
            />
            <CurrencyField
              v-model="valueAmount"
              :label="isTrackingAccount ? 'Snapshot value' : 'Valuation'"
              name="value-amount"
              data-cy="account-detail-value-amount"
            />
            <TextField v-model="valueNotes" label="Notes" name="value-notes" />
            <p class="account-detail-page__config-note">
              Saving another value for this date corrects the existing dated
              value while preserving its history.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showCutoverModal"
          title="Create richer account from tracking account"
          submit-text="Create account"
          :loading="false"
          @submit="handleCutoverSubmit"
          @cancel="showCutoverModal = false"
          @close="showCutoverModal = false"
        >
          <p class="account-detail-page__cutover-description">
            We'll create a new richer entity and retire this
            {{ cleanAccountName(account?.name) ?? account?.name }} tracking
            account effective the cutover date. This is a representation change,
            not a ledger transfer.
          </p>
          <div class="account-detail-page__cutover-form">
            <div class="account-detail-page__cutover-row">
              <div class="account-detail-page__cutover-field">
                <label class="account-detail-page__cutover-label">
                  New entity type
                </label>
                <select
                  v-model="cutoverEntityType"
                  class="account-detail-page__cutover-select"
                >
                  <option value="INVESTMENT">Investment account</option>
                  <option value="LOAN">Loan</option>
                  <option value="TANGIBLE_ASSET">Tangible asset</option>
                </select>
              </div>
              <div class="account-detail-page__cutover-field">
                <label class="account-detail-page__cutover-label">
                  Cutover date
                </label>
                <input
                  v-model="cutoverDate"
                  type="date"
                  class="account-detail-page__cutover-input"
                />
              </div>
            </div>
            <div class="account-detail-page__cutover-row">
              <div class="account-detail-page__cutover-field">
                <label class="account-detail-page__cutover-label">Name</label>
                <input
                  v-model="cutoverName"
                  type="text"
                  class="account-detail-page__cutover-input"
                />
              </div>
              <div class="account-detail-page__cutover-field">
                <label class="account-detail-page__cutover-label">
                  Opening value
                </label>
                <input
                  v-model="cutoverOpeningValue"
                  type="text"
                  class="account-detail-page__cutover-input"
                  readonly
                />
                <span class="account-detail-page__cutover-hint">
                  This value will be recorded on the cutover date.
                </span>
              </div>
            </div>
            <div class="account-detail-page__cutover-field">
              <label class="account-detail-page__cutover-label">
                Contribution category
              </label>
              <div class="account-detail-page__cutover-radios">
                <label class="account-detail-page__cutover-radio">
                  <input
                    v-model="cutoverContributionCategory"
                    type="radio"
                    value="create"
                  />
                  <span>
                    <strong>Create new</strong>
                    Create a new contribution category
                  </span>
                </label>
                <label class="account-detail-page__cutover-radio">
                  <input
                    v-model="cutoverContributionCategory"
                    type="radio"
                    value="link"
                  />
                  <span>
                    <strong>Link existing</strong>
                    Use an existing contribution category
                  </span>
                </label>
                <label class="account-detail-page__cutover-radio">
                  <input
                    v-model="cutoverContributionCategory"
                    type="radio"
                    value="none"
                  />
                  <span>
                    <strong>None</strong>
                    No contribution category
                  </span>
                </label>
              </div>
            </div>
            <label class="account-detail-page__cutover-checkbox">
              <input v-model="cutoverRepresentationConfirmed" type="checkbox" />
              <span>
                This is a representation change, not a ledger transfer. No money
                moves and no transactions are posted. We're replacing a snapshot
                with a richer account.
              </span>
            </label>
            <div class="account-detail-page__cutover-info">
              <svg
                class="account-detail-page__cutover-info-icon"
                viewBox="0 0 16 16"
                fill="none"
              >
                <circle
                  cx="8"
                  cy="8"
                  r="7"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <path
                  d="M8 5v0m0 3v4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
              <span>
                Historical as-of views before cutover use
                {{ cleanAccountName(account?.name) ?? account?.name }}. After
                the cutover date, as-of views use the new richer account.
              </span>
            </div>
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

.account-detail-page__info-banner {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-info-container);
  border: 1px solid var(--color-info);
  border-radius: var(--radius-all);
  color: var(--color-info);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__info-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.account-detail-page__snapshot-table {
  display: grid;
  max-height: clamp(360px, 52vh, 720px);
  overflow-y: auto;
}

.account-detail-page__snapshot-header {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-muted);
}

.account-detail-page__snapshot-th {
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.account-detail-page__snapshot-th--end {
  text-align: right;
}

.account-detail-page__snapshot-row {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-outline);
  align-items: center;
}

.account-detail-page__snapshot-row:last-child {
  border-bottom: none;
}

.account-detail-page__snapshot-row:hover {
  background: var(--color-surface-selected);
}

.account-detail-page__snapshot-td {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.account-detail-page__snapshot-td--end {
  text-align: right;
  justify-content: flex-end;
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.account-detail-page__snapshot-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-positive);
  flex-shrink: 0;
}

.account-detail-page__summary-sub {
  margin: 0 0 var(--space-md);
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__cutover-description {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  line-height: var(--text-body-md-line-height);
}

.account-detail-page__cutover-form {
  display: grid;
  gap: var(--space-lg);
}

.account-detail-page__cutover-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.account-detail-page__cutover-field {
  display: grid;
  gap: var(--space-xs);
}

.account-detail-page__cutover-label {
  color: var(--color-on-surface);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
}

.account-detail-page__cutover-input,
.account-detail-page__cutover-select {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
}

.account-detail-page__cutover-input:focus,
.account-detail-page__cutover-select:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.account-detail-page__cutover-input[readonly] {
  color: var(--color-on-surface-muted);
  background: var(--color-surface-muted);
}

.account-detail-page__cutover-hint {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__cutover-radios {
  display: grid;
  gap: var(--space-sm);
}

.account-detail-page__cutover-radio {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  cursor: pointer;
}

.account-detail-page__cutover-radio input {
  margin-top: 3px;
}

.account-detail-page__cutover-radio span {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  line-height: var(--text-body-md-line-height);
}

.account-detail-page__cutover-radio strong {
  display: block;
}

.account-detail-page__cutover-checkbox {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  cursor: pointer;
}

.account-detail-page__cutover-checkbox input {
  margin-top: 3px;
}

.account-detail-page__cutover-checkbox span {
  color: var(--color-on-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__cutover-info {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-info-container);
  border: 1px solid var(--color-info);
  border-radius: var(--radius-all);
  color: var(--color-info);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__cutover-info-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

@media (max-width: 900px) {
  .account-detail-page__cutover-row {
    grid-template-columns: 1fr;
  }
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
