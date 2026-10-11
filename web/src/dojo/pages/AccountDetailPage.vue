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
  ApiError,
  deleteTransaction,
  createTransaction,
  createTransfer,
  createTrackingCutover,
  createInvestmentInstrument,
  createInvestmentTransfer,
  createCreditCardPayment,
  applyReconciliation,
  createBudgetReconciliationAttempt,
  createLoanSnapshot,
  createLoanPayment,
  fetchAccountBudgetLinks,
  fetchAccountReconciliationHistory,
  fetchAccounts,
  fetchAccountBalanceTrend,
  fetchAccountTransactionSummary,
  fetchCategories,
  fetchLatestInvestmentStatement,
  fetchLoanPayments,
  fetchLoanProjection,
  fetchLoanSnapshots,
  fetchReconciliationWorkingSet,
  fetchReconciliationCommit,
  fetchTrackingSnapshots,
  fetchTangibleValuations,
  fetchTransactionsPage,
  createInvestmentReconciliationAttempt,
  fetchInvestmentInstruments,
  reconcileAccountValuation,
  reconcileLoanAccount,
  restoreTransaction,
  setAccountBudgetLink,
  type TransactionFilters,
  type BudgetReconciliationAttempt,
  type TrackingCutoverSuccessor,
  updateAccount,
  updateTransaction,
  undoLastReconciliation,
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
import InstitutionCombobox from "@/dojo/components/forms/InstitutionCombobox.vue";
import SelectField from "@/dojo/components/forms/SelectField.vue";
import TextField from "@/dojo/components/forms/TextField.vue";
import FormModal from "@/dojo/components/overlays/FormModal.vue";
import TableShell from "@/dojo/components/tables/TableShell.vue";
import TransactionFilterBar from "@/dojo/components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "@/dojo/components/transactions/TransactionLedger.vue";
import TransactionEntryForm from "@/dojo/components/transactions/TransactionEntryForm.vue";
import type { Transaction, TransactionPayload } from "@/dojo/types";
import { formatCurrency } from "@/dojo/utils/currency";
import {
  localCalendarDate,
  localCalendarDateAsTimestamp,
} from "@/dojo/utils/date";
import { institutionSuggestions } from "@/dojo/utils/institutions";
import {
  mutationErrorMessage,
  notifyMutationError,
  notifyReconciledHistoryConfirmation,
  notifyMutationSuccess,
  notifyVersionedMutationSuccess,
} from "@/dojo/state/mutationFeedback";

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const accountEntryForm = ref<InstanceType<typeof TransactionEntryForm> | null>(
  null,
);
const accountId = computed(() => route.params.id as string);
const TRANSACTION_PAGE_SIZE = 100;

const { data: accounts, isLoading: accountsLoading } = useQuery({
  queryKey: ["accounts"],
  queryFn: () => fetchAccounts(false),
});

const account = computed(() =>
  accounts.value?.find((a) => a.account_id === accountId.value),
);

const suggestedInstitutions = computed(() =>
  institutionSuggestions(accounts.value?.map((item) => item.institution) ?? []),
);

const currentDate = localCalendarDate();
const currentMonth = computed(() => currentDate.slice(0, 7));
const categoryFilter = ref("all");
const dateFilter = ref("all");
const amountFilter = ref("all");
const statusFilter = ref("all");
const chartPeriod = ref("1m");
const showConfigurationModal = ref(false);
const configurationName = ref("");
const configurationInstitution = ref("");
const configurationLast4 = ref("");
const configurationCategoryId = ref("");
const configurationRatePercent = ref("");
const configurationRateType = ref<"FIXED" | "VARIABLE">("FIXED");
const configurationScheduledPayment = ref("");
const configurationPaymentFrequency = ref<"MONTHLY" | "BIWEEKLY" | "WEEKLY">(
  "MONTHLY",
);
const configurationNextPaymentDate = ref("");
const configurationMaturityDate = ref("");
const configurationRemainingTermMonths = ref("");
const configurationExtraPrincipal = ref("");
const actionMessage = ref("");
const showValueModal = ref(false);
const valueDate = ref(localCalendarDate());
const valueAmount = ref("");
const valueNotes = ref("");
const showInvestmentStatementModal = ref(false);
const investmentStatementDate = ref(localCalendarDate());
const investmentSourceAsOf = ref(localCalendarDate());
const investmentStatementCash = ref("");
const investmentStatementTotal = ref("");
const investmentReconciliationAttempt = ref<{
  reconciliation_id: string;
  certification_allowed: boolean;
  diffs: Array<Record<string, unknown>>;
  price_only_changes: Array<Record<string, unknown>>;
} | null>(null);
const investmentReconciliationError = ref("");
const investmentReconciliationOperationId = ref(crypto.randomUUID());
const investmentHoldingRows = ref<
  Array<{
    ticker: string;
    quantity: string;
    price: string;
    averageBasis: string;
    value: string;
  }>
>([]);
const showInvestmentTransferModal = ref(false);
const investmentTransferDirection = ref<"CONTRIBUTION" | "WITHDRAWAL">(
  "CONTRIBUTION",
);
const investmentTransferDate = ref(new Date().toISOString().slice(0, 10));
const investmentTransferDestinationDate = ref(
  new Date().toISOString().slice(0, 10),
);
const investmentTransferBudgetAccountId = ref("");
const investmentTransferAmount = ref("");
const investmentTransferMemo = ref("");
const investmentTransferStatus = ref<"PENDING" | "CLEARED">("CLEARED");
const investmentTransferDestinationStatus = ref<"PENDING" | "CLEARED">(
  "CLEARED",
);
const investmentTransferOperationId = ref(crypto.randomUUID());
const showCreditCardPaymentModal = ref(false);
const creditCardPaymentSourceAccountId = ref("");
const creditCardPaymentSourceDate = ref(new Date().toISOString().slice(0, 10));
const creditCardPaymentDestinationDate = ref(
  new Date().toISOString().slice(0, 10),
);
const creditCardPaymentSourceStatus = ref<"PENDING" | "CLEARED">("CLEARED");
const creditCardPaymentDestinationStatus = ref<"PENDING" | "CLEARED">(
  "CLEARED",
);
const creditCardPaymentAmount = ref("");
const creditCardPaymentMemo = ref("Credit-card payment");
const creditCardPaymentOperationId = ref(crypto.randomUUID());
const showLoanPaymentModal = ref(false);
const loanPaymentDate = ref(new Date().toISOString().slice(0, 10));
const loanPaymentBudgetAccountId = ref("");
const loanPaymentAmount = ref("");
const loanPaymentMemo = ref("Loan payment");
const showLoanStatementModal = ref(false);
const loanStatementDate = ref(localCalendarDate());
const loanPrincipal = ref("");
const loanAccruedInterest = ref("");
const loanEscrow = ref("");
const loanUnapplied = ref("");
const loanYtdPrincipal = ref("");
const loanYtdInterest = ref("");
const showLoanAdvancedFields = ref(false);
const loanReconciliationError = ref("");
const loanMismatchNeedsCorrection = ref(false);
const showReconciliationModal = ref(false);
const showUndoReconciliationConfirmation = ref(false);
const reconciliationOperationId = ref(crypto.randomUUID());
const sourceAsOfDate = ref(localCalendarDate());
const sourceCleared = ref("");
const sourcePending = ref("");
const sourceActual = ref("");
const budgetAttempt = ref<BudgetReconciliationAttempt | null>(null);
const investigatingReconciliation = ref(false);
const showAllReconciliationTransactions = ref(false);
const persistentEditsDuringAttempt = ref(false);
const showExitWarning = ref(false);
const reconciliationMutationError = ref("");
const transactionMutationError = ref("");
const sourceBalancesBeforeEdit = ref<{
  cleared: string;
  pending: string;
  actual: string;
  attempt: BudgetReconciliationAttempt | null;
} | null>(null);

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

const {
  data: reconciliationWorkingSet,
  refetch: refetchReconciliationWorkingSet,
} = useQuery({
  queryKey: computed(() => ["reconciliation-working-set", accountId.value]),
  queryFn: () => fetchReconciliationWorkingSet(accountId.value),
  enabled: computed(() => !!account.value),
});

const {
  data: reconciliationHistory,
  isLoading: reconciliationHistoryLoading,
  isError: reconciliationHistoryError,
} = useQuery({
  queryKey: computed(() => ["account-reconciliation-history", accountId.value]),
  queryFn: async () => {
    const history = await fetchAccountReconciliationHistory(accountId.value);
    const commits = await Promise.all(
      history.items.map((item) =>
        fetchReconciliationCommit(item.reconciliation_id),
      ),
    );
    return { ...history, commits };
  },
  enabled: computed(() => !!account.value),
});

const latestUndoableReconciliation = computed(() => {
  const latest = reconciliationHistory.value?.items[0];
  if (!latest) return null;
  const isVoided = reconciliationHistory.value?.history.some(
    (event) =>
      event.event_type === "VOID" &&
      event.reconciliation_id === latest.reconciliation_id,
  );
  return isVoided || latest.undone ? null : latest;
});
const reconciliationAttention = computed(() => {
  const response = reconciliationWorkingSet.value as
    | {
        attention?: {
          changes_since?: number;
          carried_pending?: number;
          reconciled_history_changed?: number;
        };
      }
    | undefined;
  return response?.attention;
});

const workingSetItems = computed(
  () =>
    (
      reconciliationWorkingSet.value as
        | {
            items?: Array<{
              transaction_id: string;
              classification: string;
              baseline: Record<string, unknown> | null;
              current: Record<string, unknown> | null;
              changed_fields: string[];
            }>;
          }
        | undefined
    )?.items ?? [],
);
const workingSetByTransactionId = computed(
  () =>
    new Map(workingSetItems.value.map((item) => [item.transaction_id, item])),
);
const reconciliationChanges = computed(() =>
  Object.fromEntries(
    workingSetItems.value.flatMap((item) => {
      const label =
        item.classification === "NEW" || item.classification === "RESTORED"
          ? "Added"
          : item.classification === "EDITED" ||
              item.classification === "PENDING_CLEARED"
            ? "Edited"
            : item.classification === "REMOVED"
              ? "Removed"
              : null;
      return label
        ? [
            [
              item.transaction_id,
              {
                label,
                changedFields: item.changed_fields,
                removed: item.classification === "REMOVED",
                details: item.changed_fields
                  .map((field) => {
                    const formatValue = (value: unknown) => {
                      if (value == null) return "—";
                      if (
                        field === "amount_minor" &&
                        typeof value === "number"
                      ) {
                        return formatCurrency(value);
                      }
                      return String(value);
                    };
                    const fieldLabel =
                      field === "amount_minor"
                        ? "Amount"
                        : field === "status"
                          ? "Status"
                          : field;
                    return `${fieldLabel}: ${formatValue(item.baseline?.[field])} → ${formatValue(item.current?.[field])}`;
                  })
                  .join("; "),
              },
            ],
          ]
        : [];
    }),
  ),
);
const removedReconciliationItems = computed(() =>
  workingSetItems.value.filter((item) => item.classification === "REMOVED"),
);
const removedReconciliationTransactions = computed(() =>
  removedReconciliationItems.value.flatMap((item): Transaction[] => {
    const baseline = item.baseline;
    if (!baseline) return [];

    const transactionAccountId = String(baseline.account_id ?? accountId.value);
    const categoryId =
      typeof baseline.category_id === "string" ? baseline.category_id : null;
    const systemCategory =
      (
        [
          "TX_AVAILABLE_TO_BUDGET",
          "TX_ACCOUNT_TRANSFER",
          "TX_STARTING_BALANCE",
          "TX_BALANCE_ADJUSTMENT",
          "TX_UNCATEGORIZED",
        ] as const
      ).find((candidate) => candidate === baseline.system_category) ?? null;

    return [
      {
        transaction_id: item.transaction_id,
        version: String(baseline.row_id ?? item.transaction_id),
        date: String(baseline.date ?? ""),
        account_id: transactionAccountId,
        account_name:
          accounts.value?.find(
            (candidate) => candidate.account_id === transactionAccountId,
          )?.name ?? "",
        amount_minor: Number(baseline.amount_minor ?? 0),
        category_id: categoryId,
        category_name:
          categories.value.find(
            (category) => category.category_id === categoryId,
          )?.name ?? null,
        system_category: systemCategory,
        status: baseline.status === "PENDING" ? "PENDING" : "CLEARED",
        memo: String(baseline.memo ?? ""),
        is_hidden_entity: false,
      },
    ];
  }),
);
const investigationTransactions = computed(() =>
  [
    ...(showAllReconciliationTransactions.value
      ? transactions.value
      : transactions.value.filter((item) => {
          const change = workingSetByTransactionId.value.get(
            item.transaction_id,
          );
          return !!change;
        })),
    ...removedReconciliationTransactions.value,
  ].sort((left, right) => right.date.localeCompare(left.date)),
);

const sourceBalanceInputs = computed(() => [
  { key: "cleared" as const, value: sourceCleared.value },
  { key: "pending" as const, value: sourcePending.value },
  { key: "actual" as const, value: sourceActual.value },
]);
const enteredSourceBalances = computed(() =>
  sourceBalanceInputs.value.flatMap(({ key, value }) => {
    const minor = value.trim() ? parseSourceBalanceMinor(value) : null;
    return minor === null ? [] : [{ key, minor }];
  }),
);
const derivedSourceBalance = computed(() => {
  if (enteredSourceBalances.value.length !== 2) return null;
  const values = Object.fromEntries(
    enteredSourceBalances.value.map(({ key, minor }) => [key, minor]),
  ) as Partial<Record<"cleared" | "pending" | "actual", number>>;
  if (values.cleared === undefined)
    return { key: "cleared" as const, minor: values.actual! - values.pending! };
  if (values.pending === undefined)
    return { key: "pending" as const, minor: values.actual! - values.cleared };
  return { key: "actual" as const, minor: values.cleared + values.pending };
});
const sourceEntryReady = computed(
  () => enteredSourceBalances.value.length === 2,
);
const certificationAllowed = computed(
  () => budgetAttempt.value?.certification_allowed ?? false,
);
const budgetReconciliationSubmitText = computed(() =>
  budgetAttempt.value
    ? certificationAllowed.value
      ? "Reconcile account"
      : "Review differences"
    : "Compare balances",
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
const isCreditCardAccount = computed(
  () =>
    isBudgetAccount.value &&
    account.value?.budget_account_type === "CREDIT_CARD",
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

const { data: investmentInstruments } = useQuery({
  queryKey: ["investment-instruments"],
  queryFn: fetchInvestmentInstruments,
  enabled: computed(() => isInvestmentAccount.value),
});

const { data: accountBudgetLinks } = useQuery({
  queryKey: computed(() => ["account-budget-links", accountId.value]),
  queryFn: () => fetchAccountBudgetLinks(accountId.value),
  enabled: computed(
    () =>
      !!accountId.value && (isInvestmentAccount.value || isLoanAccount.value),
  ),
});
const { data: loanSnapshots, isLoading: loanSnapshotsLoading } = useQuery({
  queryKey: computed(() => ["loan-snapshots", accountId.value]),
  queryFn: () => fetchLoanSnapshots(accountId.value),
  enabled: computed(() => !!accountId.value && isLoanAccount.value),
});
const { data: loanPayments } = useQuery({
  queryKey: computed(() => ["loan-payments", accountId.value]),
  queryFn: () => fetchLoanPayments(accountId.value),
  enabled: computed(() => !!accountId.value && isLoanAccount.value),
});
const { data: loanProjection } = useQuery({
  queryKey: computed(() => ["loan-projection", accountId.value]),
  queryFn: () => fetchLoanProjection(accountId.value),
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
const configurableCategoryOptions = computed(() =>
  isInvestmentAccount.value && !linkedContributionCategoryId.value
    ? [
        { value: "", label: "Do not link a category yet" },
        ...contributionCategoryOptions.value,
      ]
    : contributionCategoryOptions.value,
);
const selectedContributionCategory = computed(() =>
  categories.value.find(
    (category) => category.category_id === linkedContributionCategoryId.value,
  ),
);
const selectedLoanCategory = computed(() =>
  categories.value.find(
    (category) => category.category_id === linkedLoanCategoryId.value,
  ),
);
const contributionPreview = computed(() => {
  const available = selectedContributionCategory.value?.available_minor ?? 0;
  const amount = parseCurrencyMinor(investmentTransferAmount.value) ?? 0;
  return {
    available,
    amount,
    resultingAvailable: available - amount,
  };
});
const loanProjectionColumns = [
  { key: "date", label: "Payment date" },
  { key: "payment", label: "Payment", align: "end" as const },
  { key: "principal", label: "Principal", align: "end" as const },
  { key: "interest", label: "Interest", align: "end" as const },
  { key: "balance", label: "Balance", align: "end" as const },
];
const loanProjectionRows = computed(() =>
  (loanProjection.value?.rows ?? []).slice(0, 12).map((row) => ({
    key: row.payment_number,
    date: row.payment_date,
    payment: formatCurrency(row.payment_minor),
    principal: formatCurrency(row.principal_minor),
    interest: formatCurrency(row.interest_minor),
    balance: formatCurrency(row.remaining_principal_minor),
  })),
);

const valueHistory = computed(() =>
  isTrackingAccount.value
    ? (trackingSnapshots.value ?? [])
    : (tangibleValuations.value ?? []),
);

const showCutoverModal = ref(false);
const cutoverDate = ref(new Date().toISOString().slice(0, 10));
const cutoverRepresentationConfirmed = ref(true);
const cutoverOperationId = ref("");
const cutoverFinalTrackingValue = ref("");
type CutoverHoldingDraft = {
  ticker: string;
  quantity: string;
  price: string;
  averageBasis: string;
};
type CutoverSuccessorDraft = {
  id: string;
  accountClass: "INVESTMENT" | "LOAN" | "TANGIBLE_ASSET";
  name: string;
  institution: string;
  openingValue: string;
  escrow: string;
  accruedInterest: string;
  unappliedCredit: string;
  categoryId: string;
  holdings: CutoverHoldingDraft[];
};
const cutoverSuccessors = ref<CutoverSuccessorDraft[]>([]);

function newCutoverSuccessor(
  openingValue = "",
  name = "New successor",
): CutoverSuccessorDraft {
  return {
    id: crypto.randomUUID(),
    accountClass: "INVESTMENT",
    name,
    institution: account.value?.institution ?? "",
    openingValue,
    escrow: "0",
    accruedInterest: "",
    unappliedCredit: "",
    categoryId: "",
    holdings: [],
  };
}

function cutoverHoldingValue(holding: CutoverHoldingDraft): number {
  const quantityMicros = Math.round(Number(holding.quantity) * 1_000_000);
  const price = parseCurrencyMinor(holding.price) ?? 0;
  return Math.floor((quantityMicros * price + 500_000) / 1_000_000);
}

const cutoverInvestmentCashTotal = computed(() =>
  cutoverSuccessors.value.reduce(
    (total, successor) =>
      successor.accountClass === "INVESTMENT"
        ? total + (parseCurrencyMinor(successor.openingValue) ?? 0)
        : total,
    0,
  ),
);

const cutoverInvestmentHoldingsTotal = computed(() =>
  cutoverSuccessors.value.reduce(
    (total, successor) =>
      successor.accountClass === "INVESTMENT"
        ? total +
          successor.holdings.reduce(
            (holdingTotal, holding) =>
              holdingTotal + cutoverHoldingValue(holding),
            0,
          )
        : total,
    0,
  ),
);

const hasCutoverInvestmentSuccessor = computed(() =>
  cutoverSuccessors.value.some(
    (successor) => successor.accountClass === "INVESTMENT",
  ),
);

const cutoverSuccessorTotal = computed(() =>
  cutoverSuccessors.value.reduce((total, successor) => {
    const opening = parseCurrencyMinor(successor.openingValue) ?? 0;
    if (successor.accountClass === "LOAN") {
      return (
        total -
        opening -
        (parseCurrencyMinor(successor.accruedInterest) ?? 0) +
        (parseCurrencyMinor(successor.escrow) ?? 0) +
        (parseCurrencyMinor(successor.unappliedCredit) ?? 0)
      );
    }
    if (successor.accountClass === "INVESTMENT") {
      return (
        total +
        opening +
        successor.holdings.reduce(
          (holdingTotal, holding) =>
            holdingTotal + cutoverHoldingValue(holding),
          0,
        )
      );
    }
    return total + opening;
  }, 0),
);
const cutoverExpectedSignedValue = computed(() => {
  const value = parseCurrencyMinor(cutoverFinalTrackingValue.value) ?? 0;
  return account.value?.tracking_polarity === "LIABILITY" ? -value : value;
});
const cutoverVariance = computed(
  () => cutoverSuccessorTotal.value - cutoverExpectedSignedValue.value,
);
const cutoverDifferenceDescription = computed(() => {
  if (cutoverVariance.value === 0) return "Exact match";
  const amount = formatCurrency(Math.abs(cutoverVariance.value));
  if (cutoverVariance.value > 0) {
    return `Successor total is ${amount} above the final tracking value. Reduce asset or cash values, or increase liability values, by ${amount}.`;
  }
  return `Successor total is ${amount} below the final tracking value. Increase asset or cash values, or reduce liability values, by ${amount}.`;
});
const cutoverCanSave = computed(
  () =>
    cutoverRepresentationConfirmed.value &&
    parseCurrencyMinor(cutoverFinalTrackingValue.value) !== null &&
    cutoverVariance.value === 0 &&
    cutoverSuccessors.value.length > 0 &&
    cutoverSuccessors.value.every(
      (successor) =>
        successor.name.trim().length > 0 &&
        parseCurrencyMinor(successor.openingValue) !== null &&
        (successor.accountClass !== "LOAN" ||
          successor.categoryId.length > 0) &&
        (successor.accountClass !== "INVESTMENT" ||
          successor.holdings.every(
            (holding) =>
              holding.ticker.trim().length > 0 &&
              Number.isFinite(Number(holding.quantity)) &&
              Number(holding.quantity) >= 0 &&
              (parseCurrencyMinor(holding.price) ?? 0) > 0 &&
              parseCurrencyMinor(holding.averageBasis) !== null,
          )),
    ),
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
        auxValue:
          investigatingReconciliation.value && budgetAttempt.value
            ? `Source ${formatCurrency(budgetAttempt.value.source.actual_minor)} · Δ ${formatCurrency(budgetAttempt.value.deltas.actual_delta_minor)}`
            : `As of ${formatDateShort()}`,
      },
      {
        key: "pending",
        label: "Pending",
        value: formatCurrency(account.value.pending_balance_minor),
        auxValue:
          investigatingReconciliation.value && budgetAttempt.value
            ? `Source ${formatCurrency(budgetAttempt.value.source.pending_minor)} · Δ ${formatCurrency(budgetAttempt.value.deltas.pending_delta_minor)}`
            : `${transactionStatusCounts.value.PENDING} transactions`,
        status: { label: "", variant: "warning" as const },
      },
      {
        key: "cleared",
        label: "Cleared",
        value: formatCurrency(account.value.cleared_balance_minor),
        auxValue:
          investigatingReconciliation.value && budgetAttempt.value
            ? `Source ${formatCurrency(budgetAttempt.value.source.cleared_minor)} · Δ ${formatCurrency(budgetAttempt.value.deltas.cleared_delta_minor)}`
            : `${transactionStatusCounts.value.CLEARED} transactions`,
        status: { label: "", variant: "positive" as const },
      },
      {
        key: "net-worth",
        label: "Net worth contribution",
        value: formatCurrency(account.value.display_balance_minor),
        auxValue: "Assets",
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
        key: "freshness",
        label: "Snapshot freshness",
        value: account.value.latest_valuation_date
          ? "Current"
          : "Missing snapshot",
        auxValue: account.value.latest_valuation_date
          ? `As of ${latestSnapshotDate}`
          : "Add a snapshot to establish value",
        status: account.value.latest_valuation_date
          ? { label: "", variant: "positive" as const }
          : { label: "", variant: "warning" as const },
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

const reconciliationCommitById = computed(
  () =>
    new Map(
      (reconciliationHistory.value?.commits ?? []).map((commit) => [
        commit.reconciliation_id,
        commit,
      ]),
    ),
);

function reconciliationEvidenceSummary(reconciliationId: string): string {
  const commit = reconciliationCommitById.value.get(reconciliationId);
  const evidence = commit?.evidence;
  if (!evidence) return "Evidence recorded";
  const payload = evidence.normalized_payload;
  const source = payload.source;
  if (typeof source === "object" && source !== null) {
    const sourceRecord = source as Record<string, unknown>;
    const cash = sourceRecord.cash_minor;
    const total = sourceRecord.total_value_minor;
    const positions = sourceRecord.positions;
    if (typeof cash === "number" && typeof total === "number") {
      return `Cash ${formatCurrency(cash)} · ${Array.isArray(positions) ? positions.length : 0} positions · Total ${formatCurrency(total)}`;
    }
  }
  const loanFacts = payload.source_facts;
  if (typeof loanFacts === "object" && loanFacts !== null) {
    const facts = loanFacts as Record<string, unknown>;
    const reported = [
      ["Principal", facts.principal_balance_minor],
      ["Interest", facts.accrued_interest_minor],
      ["Escrow", facts.escrow_balance_minor],
    ].flatMap(([label, value]) =>
      typeof value === "number" ? [`${label} ${formatCurrency(value)}`] : [],
    );
    if (reported.length) return reported.join(" · ");
  }
  if (typeof payload.value_minor === "number") {
    const details = [`Value ${formatCurrency(payload.value_minor)}`];
    if (typeof payload.source === "string") details.push(payload.source);
    if (typeof payload.notes === "string" && payload.notes.trim()) {
      details.push(payload.notes.trim());
    }
    return details.join(" · ");
  }
  const values = [
    ["Cleared", payload.cleared_minor],
    ["Pending", payload.pending_minor],
    ["Actual", payload.actual_minor],
  ].flatMap(([label, value]) =>
    typeof value === "number" ? [`${label} ${formatCurrency(value)}`] : [],
  );
  return values.length ? values.join(" · ") : evidence.evidence_kind;
}

function formatReconciliationDate(value: string): string {
  return formatDateShort(new Date(`${value.slice(0, 10)}T00:00:00`));
}

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
  { label: "Imported from", value: "Aspire Budgeting" },
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
  if (
    isInvestmentAccount.value &&
    account.value?.provisional_value_minor !== undefined &&
    account.value.provisional_value_minor !== 0
  ) {
    return `Provisional after ${formatDateShort(new Date(`${effectiveDate}T00:00:00`))}`;
  }
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
    openReconciliationModal();
  }
  if (key === "edit-configuration") {
    openConfigurationModal();
  }
};

const updateTransactionMutation = useMutation({
  mutationFn: ({
    id,
    payload,
    expectedVersion,
  }: {
    id: string;
    payload: TransactionPayload;
    expectedVersion: string;
  }) =>
    updateTransaction(id, payload, expectedVersion, {
      acknowledgeReconciledHistoryChange: investigatingReconciliation.value,
    }),
  onSuccess: () => {
    transactionMutationError.value = "";
    invalidateAccountDetailQueries();
    if (investigatingReconciliation.value) {
      persistentEditsDuringAttempt.value = true;
      void refreshReconciliationAfterMutation();
    }
  },
  onError: (error) => {
    if (
      error instanceof ApiError &&
      error.code === "reconciled_history_change_requires_confirmation"
    ) {
      transactionMutationError.value = "";
      return;
    }
    transactionMutationError.value = mutationErrorMessage(error);
  },
});

const deleteTransactionMutation = useMutation({
  mutationFn: ({
    id,
    expectedVersion,
  }: {
    id: string;
    expectedVersion: string;
  }) =>
    deleteTransaction(id, expectedVersion, {
      acknowledgeReconciledHistoryChange: investigatingReconciliation.value,
    }),
  onSuccess: () => {
    invalidateAccountDetailQueries();
    if (investigatingReconciliation.value) {
      persistentEditsDuringAttempt.value = true;
      void refreshReconciliationAfterMutation();
    }
  },
});

const updateAccountMutation = useMutation({
  mutationFn: async ({
    id,
    payload,
    linkChange,
  }: {
    id: string;
    payload: Record<string, unknown>;
    linkChange?: {
      action: "set";
      payload: Parameters<typeof setAccountBudgetLink>[1];
    };
  }) => {
    await updateAccount(id, payload);
    if (linkChange?.action === "set") {
      await setAccountBudgetLink(id, linkChange.payload);
    }
  },
  onSuccess: () => {
    showConfigurationModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["account-budget-links"] });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Account updated");
  },
});
const createValueMutation = useMutation({
  mutationFn: (payload: {
    effective_date: string;
    amount_minor: number;
    source: string;
    notes: string;
    client_operation_id: string;
  }) => reconcileAccountValuation(accountId.value, payload),
  onSuccess: () => {
    showValueModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["tracking-snapshots"] });
    queryClient.invalidateQueries({ queryKey: ["tangible-valuations"] });
    queryClient.invalidateQueries({
      queryKey: ["account-reconciliation-history", accountId.value],
    });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Valuation reconciled");
  },
});
const cutoverMutation = useMutation({
  mutationFn: (payload: Parameters<typeof createTrackingCutover>[1]) =>
    createTrackingCutover(accountId.value, payload),
  onSuccess: async (result) => {
    showCutoverModal.value = false;
    actionMessage.value =
      result.cutover_date > currentDate
        ? `Representation cutover scheduled for ${result.cutover_date}. The tracking account remains current until then.`
        : "Representation cutover recorded. No ledger transactions were created.";
    if (result.cutover_date <= currentDate) {
      if (result.successor_account_ids.length === 1) {
        await router.replace(
          `/assets-liabilities/${result.successor_account_ids[0]}`,
        );
      } else {
        await router.replace("/assets-liabilities");
      }
    }
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Tracking account replaced");
  },
});
const investmentAttemptMutation = useMutation({
  mutationFn: async () => {
    const cash = parseCurrencyMinor(investmentStatementCash.value);
    const total = parseCurrencyMinor(investmentStatementTotal.value);
    if (cash === null || total === null) {
      throw new Error("Enter source cash and total account value.");
    }
    const knownInstruments = [...(investmentInstruments.value ?? [])];
    const positions = await Promise.all(
      investmentHoldingRows.value.map(async (holding) => {
        const symbol = holding.ticker.trim().toUpperCase();
        let instrument = knownInstruments.find(
          (candidate) => candidate.symbol?.toUpperCase() === symbol,
        );
        if (!instrument) {
          instrument = await createInvestmentInstrument({
            symbol,
            name: symbol,
          });
          knownInstruments.push(instrument);
        }
        const quantityMicros = Math.round(Number(holding.quantity) * 1_000_000);
        const unitBasis = parseCurrencyMinor(holding.averageBasis);
        const price = parseCurrencyMinor(holding.price);
        const value = parseCurrencyMinor(holding.value);
        if (unitBasis === null || price === null || value === null) {
          throw new Error(
            "Enter each holding’s basis, price, and reported value.",
          );
        }
        return {
          instrument_id: instrument.instrument_id,
          quantity_micros: quantityMicros,
          total_cost_basis_minor: Math.floor(
            (quantityMicros * unitBasis + 500_000) / 1_000_000,
          ),
          source_price_minor: price,
          source_value_minor: value,
        };
      }),
    );
    return createInvestmentReconciliationAttempt(accountId.value, {
      source_kind: "INVESTMENT_STATEMENT",
      cutoff: investmentStatementDate.value,
      source_as_of: localCalendarDateAsTimestamp(investmentSourceAsOf.value),
      source_cash_minor: cash,
      source_total_value_minor: total,
      source_positions: positions,
    });
  },
  onSuccess: (result) => {
    investmentReconciliationAttempt.value =
      result as typeof investmentReconciliationAttempt.value;
    investmentReconciliationError.value = "";
  },
  onError: (error) => {
    investmentReconciliationError.value = mutationErrorMessage(error);
  },
});
const investmentApplyMutation = useMutation({
  mutationFn: () => {
    const attempt = investmentReconciliationAttempt.value;
    if (!attempt) throw new Error("Compare the statement before reconciling.");
    if (!attempt.certification_allowed) {
      throw new Error("Investigate the canonical holdings before reconciling.");
    }
    return applyReconciliation(attempt.reconciliation_id, {
      client_operation_id: investmentReconciliationOperationId.value,
    });
  },
  onSuccess: () => {
    showInvestmentStatementModal.value = false;
    investmentReconciliationAttempt.value = null;
    queryClient.invalidateQueries({ queryKey: ["investment-statement"] });
    queryClient.invalidateQueries({
      queryKey: ["account-reconciliation-history", accountId.value],
    });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Account reconciled");
  },
  onError: (error) => {
    investmentReconciliationError.value = mutationErrorMessage(error);
  },
});
watch(
  [
    investmentStatementDate,
    investmentSourceAsOf,
    investmentStatementCash,
    investmentStatementTotal,
    investmentHoldingRows,
  ],
  () => {
    if (!showInvestmentStatementModal.value) return;
    investmentReconciliationAttempt.value = null;
    investmentReconciliationError.value = "";
  },
  { deep: true },
);
const investmentTransferMutation = useMutation({
  mutationFn: (payload: Parameters<typeof createInvestmentTransfer>[1]) =>
    createInvestmentTransfer(accountId.value, payload),
  onSuccess: () => {
    showInvestmentTransferModal.value = false;
    queryClient.invalidateQueries({ queryKey: ["account-budget-links"] });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Investment transfer recorded");
  },
});
const creditCardPaymentMutation = useMutation({
  mutationFn: (payload: Parameters<typeof createCreditCardPayment>[1]) =>
    createCreditCardPayment(accountId.value, payload),
  onSuccess: () => {
    showCreditCardPaymentModal.value = false;
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Card payment recorded");
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
    notifyMutationSuccess("Loan payment recorded");
  },
});
function loanReconciliationPayload(): Parameters<
  typeof reconcileLoanAccount
>[1] {
  const principal = parseCurrencyMinor(loanPrincipal.value);
  if (principal === null) throw new Error("Enter principal balance.");
  const accruedInterest = parseCurrencyMinor(loanAccruedInterest.value);
  const escrow = parseCurrencyMinor(loanEscrow.value);
  const unappliedCredit = parseCurrencyMinor(loanUnapplied.value);
  const ytdPrincipal = parseCurrencyMinor(loanYtdPrincipal.value);
  const ytdInterest = parseCurrencyMinor(loanYtdInterest.value);
  return {
    source_as_of: localCalendarDateAsTimestamp(loanStatementDate.value),
    source_adapter: "manual",
    principal_balance_minor: principal,
    ...(accruedInterest === null
      ? {}
      : { accrued_interest_minor: accruedInterest }),
    ...(escrow === null ? {} : { escrow_balance_minor: escrow }),
    ...(unappliedCredit === null
      ? {}
      : { unapplied_credit_minor: unappliedCredit }),
    ...(ytdPrincipal === null
      ? {}
      : { ytd_principal_paid_minor: ytdPrincipal }),
    ...(ytdInterest === null ? {} : { ytd_interest_paid_minor: ytdInterest }),
  };
}

const loanStatementMutation = useMutation({
  mutationFn: (payload: Parameters<typeof reconcileLoanAccount>[1]) =>
    reconcileLoanAccount(accountId.value, payload),
  onSuccess: () => {
    showLoanStatementModal.value = false;
    loanReconciliationError.value = "";
    loanMismatchNeedsCorrection.value = false;
    queryClient.invalidateQueries({ queryKey: ["loan-snapshots"] });
    queryClient.invalidateQueries({
      queryKey: ["account-reconciliation-history", accountId.value],
    });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Account reconciled");
  },
  onError: (error) => {
    const detail = error instanceof ApiError ? error.detail : null;
    const mismatch =
      typeof detail === "object" &&
      detail !== null &&
      "code" in detail &&
      detail.code === "loan_snapshot_mismatch";
    loanMismatchNeedsCorrection.value = mismatch;
    loanReconciliationError.value = mismatch
      ? "Lender facts differ from the canonical snapshot. Review and correct the canonical snapshot before reconciling."
      : mutationErrorMessage(error);
  },
});
const correctLoanSnapshotMutation = useMutation({
  mutationFn: async () => {
    const payload = loanReconciliationPayload();
    const {
      principal_balance_minor,
      accrued_interest_minor,
      escrow_balance_minor,
      unapplied_credit_minor,
      ytd_principal_paid_minor,
      ytd_interest_paid_minor,
    } = payload;
    await createLoanSnapshot(accountId.value, {
      effective_date: loanStatementDate.value,
      principal_balance_minor,
      ...(accrued_interest_minor === undefined
        ? {}
        : { accrued_interest_minor }),
      ...(escrow_balance_minor === undefined ? {} : { escrow_balance_minor }),
      ...(unapplied_credit_minor === undefined
        ? {}
        : { unapplied_credit_minor }),
      ...(ytd_principal_paid_minor === undefined
        ? {}
        : { ytd_principal_paid_minor }),
      ...(ytd_interest_paid_minor === undefined
        ? {}
        : { ytd_interest_paid_minor }),
    });
    return reconcileLoanAccount(accountId.value, payload);
  },
  onSuccess: () => {
    showLoanStatementModal.value = false;
    loanReconciliationError.value = "";
    loanMismatchNeedsCorrection.value = false;
    queryClient.invalidateQueries({ queryKey: ["loan-snapshots"] });
    queryClient.invalidateQueries({
      queryKey: ["account-reconciliation-history", accountId.value],
    });
    invalidateAccountDetailQueries();
    notifyMutationSuccess("Account reconciled");
  },
  onError: (error) => {
    loanReconciliationError.value = mutationErrorMessage(error);
  },
});
const budgetAttemptMutation = useMutation({
  mutationFn: () => {
    const values = Object.fromEntries(
      enteredSourceBalances.value.map(({ key, minor }) => [
        `source_${key}_minor`,
        minor,
      ]),
    );
    return createBudgetReconciliationAttempt(accountId.value, {
      source_kind: isCreditCardAccount.value
        ? "CREDIT_CARD_STATEMENT"
        : "BANK_STATEMENT",
      cutoff: sourceAsOfDate.value,
      source_as_of: localCalendarDateAsTimestamp(sourceAsOfDate.value),
      ...values,
    } as Parameters<typeof createBudgetReconciliationAttempt>[1]);
  },
  onSuccess: (attempt) => {
    if ("certification_allowed" in attempt) budgetAttempt.value = attempt;
    else
      reconciliationMutationError.value = "Could not prepare budget balances.";
  },
  onError: (error) => {
    reconciliationMutationError.value = mutationErrorMessage(error);
  },
});
let budgetAttemptTimeout: ReturnType<typeof setTimeout> | undefined;
watch(
  [
    sourceCleared,
    sourcePending,
    sourceActual,
    sourceAsOfDate,
    sourceEntryReady,
  ],
  () => {
    clearTimeout(budgetAttemptTimeout);
    budgetAttempt.value = null;
    if (
      !showReconciliationModal.value ||
      !isBudgetAccount.value ||
      !sourceEntryReady.value
    )
      return;
    budgetAttemptTimeout = setTimeout(
      () => budgetAttemptMutation.mutate(),
      350,
    );
  },
);
const budgetApplyMutation = useMutation({
  mutationFn: () => {
    if (!budgetAttempt.value) throw new Error("Enter source balances first");
    return applyReconciliation(budgetAttempt.value.reconciliation_id, {
      client_operation_id: reconciliationOperationId.value,
    });
  },
  onSuccess: () => {
    showReconciliationModal.value = false;
    budgetAttempt.value = null;
    investigatingReconciliation.value = false;
    persistentEditsDuringAttempt.value = false;
    sourceBalancesBeforeEdit.value = null;
    invalidateAccountDetailQueries();
    queryClient.invalidateQueries({
      queryKey: ["account-reconciliation-history", accountId.value],
    });
    notifyMutationSuccess("Account reconciled");
  },
  onError: (error) => {
    reconciliationMutationError.value = mutationErrorMessage(error);
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
  queryClient.invalidateQueries({ queryKey: ["reconciliation-working-set"] });
  queryClient.invalidateQueries({ queryKey: ["transactions"] });
  queryClient.invalidateQueries({ queryKey: ["accounts"] });
  queryClient.invalidateQueries({ queryKey: ["account-transaction-summary"] });
  queryClient.invalidateQueries({ queryKey: ["account-balance-trend"] });
  queryClient.invalidateQueries({ queryKey: ["assets-liabilities"] });
  queryClient.invalidateQueries({ queryKey: ["budget"] });
  queryClient.invalidateQueries({ queryKey: ["allocations"] });
  queryClient.invalidateQueries({ queryKey: ["net-worth"] });
  queryClient.invalidateQueries({ queryKey: ["category-activity"] });
  queryClient.invalidateQueries({ queryKey: ["loan-projection"] });
  queryClient.invalidateQueries({ queryKey: ["available-to-budget"] });
}

function openValueModal() {
  valueDate.value = localCalendarDate();
  valueAmount.value = "";
  valueNotes.value = "";
  showValueModal.value = true;
}

function openReconciliationModal() {
  reconciliationOperationId.value = crypto.randomUUID();
  sourceAsOfDate.value = localCalendarDate();
  sourceCleared.value = "";
  sourcePending.value = "";
  sourceActual.value = "";
  budgetAttempt.value = null;
  reconciliationMutationError.value = "";
  sourceBalancesBeforeEdit.value = null;
  showReconciliationModal.value = true;
}

function previewBudgetBalances() {
  budgetAttemptMutation.mutate();
}

function sourceInputValue(key: "cleared" | "pending" | "actual") {
  if (derivedSourceBalance.value?.key === key) {
    return (derivedSourceBalance.value.minor / 100).toFixed(2);
  }

  return key === "cleared"
    ? sourceCleared.value
    : key === "pending"
      ? sourcePending.value
      : sourceActual.value;
}

function sourceInputDisabled(key: "cleared" | "pending" | "actual") {
  return derivedSourceBalance.value?.key === key;
}

function editSourceBalances() {
  sourceBalancesBeforeEdit.value = {
    cleared: sourceCleared.value,
    pending: sourcePending.value,
    actual: sourceActual.value,
    attempt: budgetAttempt.value,
  };
  showReconciliationModal.value = true;
  reconciliationMutationError.value = "";
}

function cancelReconciliationEntry() {
  showReconciliationModal.value = false;
  if (investigatingReconciliation.value && sourceBalancesBeforeEdit.value) {
    sourceCleared.value = sourceBalancesBeforeEdit.value.cleared;
    sourcePending.value = sourceBalancesBeforeEdit.value.pending;
    sourceActual.value = sourceBalancesBeforeEdit.value.actual;
    budgetAttempt.value = sourceBalancesBeforeEdit.value.attempt;
  }
  sourceBalancesBeforeEdit.value = null;
}

function reviewReconciliationDifferences() {
  showReconciliationModal.value = false;
  sourceBalancesBeforeEdit.value = null;
  investigatingReconciliation.value = true;
  showAllReconciliationTransactions.value = false;
  persistentEditsDuringAttempt.value = false;
  void refetchReconciliationWorkingSet();
}

function exitReconciliation() {
  if (persistentEditsDuringAttempt.value) {
    showExitWarning.value = true;
    return;
  }
  investigatingReconciliation.value = false;
  budgetAttempt.value = null;
}

function confirmExitReconciliation() {
  showExitWarning.value = false;
  investigatingReconciliation.value = false;
  budgetAttempt.value = null;
}

async function confirmUndoLastReconciliation() {
  const latest = latestUndoableReconciliation.value;
  if (!latest) return;
  await undoLastReconciliation(
    accountId.value,
    latest.reconciliation_id,
    crypto.randomUUID(),
  );
  showUndoReconciliationConfirmation.value = false;
  await queryClient.invalidateQueries({
    queryKey: ["account-reconciliation-history", accountId.value],
  });
  invalidateAccountDetailQueries();
  notifyMutationSuccess("Reconciliation undone");
}

async function refreshReconciliationAfterMutation() {
  if (!investigatingReconciliation.value || !sourceEntryReady.value) return;
  await queryClient.invalidateQueries({ queryKey: ["accounts"] });
  await queryClient.invalidateQueries({ queryKey: ["transactions"] });
  await refetchReconciliationWorkingSet();
  budgetAttemptMutation.mutate();
}

function handleAccountEntry(
  payload: TransactionPayload | Record<string, unknown>,
) {
  if ("kind" in payload && payload.kind === "transfer") {
    const transfer = payload as {
      date: string;
      from_account_id: string;
      to_account_id: string;
      amount_minor: number;
      status: "PENDING" | "CLEARED";
      memo: string;
      to_account_date: string;
      to_account_status: "PENDING" | "CLEARED";
      to_account_memo: string;
    };
    void createTransfer({
      date: transfer.date,
      from_account_id: transfer.from_account_id,
      to_account_id: transfer.to_account_id,
      amount_minor: transfer.amount_minor,
      status: transfer.status,
      memo: transfer.memo,
      source_date: transfer.date,
      source_status: transfer.status,
      source_memo: transfer.memo,
      destination_date: transfer.to_account_date,
      destination_status: transfer.to_account_status,
      destination_memo: transfer.to_account_memo,
    })
      .then(() => {
        accountEntryForm.value?.resetForm();
        invalidateAccountDetailQueries();
        notifyMutationSuccess("Transfer added");
        const affectsAccount =
          transfer.from_account_id === accountId.value ||
          transfer.to_account_id === accountId.value;
        if (investigatingReconciliation.value && affectsAccount) {
          persistentEditsDuringAttempt.value = true;
          void refreshReconciliationAfterMutation();
        }
      })
      .catch((error: unknown) => {
        notifyMutationError(error);
      });
    return;
  }
  void createTransaction(payload as TransactionPayload)
    .then((created) => {
      accountEntryForm.value?.resetForm();
      invalidateAccountDetailQueries();
      notifyVersionedMutationSuccess(
        "Transaction added",
        "Transaction addition undone",
        {
          key: `transaction:${created.transaction_id}`,
          version: created.version,
          run: async (expectedVersion) => {
            await deleteTransaction(created.transaction_id, expectedVersion, {
              acknowledgeReconciledHistoryChange: true,
            });
            invalidateAccountDetailQueries();
            if (investigatingReconciliation.value) {
              persistentEditsDuringAttempt.value = true;
              await refreshReconciliationAfterMutation();
            }
          },
        },
      );
      if (
        investigatingReconciliation.value &&
        (payload as TransactionPayload).account_id === accountId.value
      ) {
        persistentEditsDuringAttempt.value = true;
        void refreshReconciliationAfterMutation();
      }
    })
    .catch((error: unknown) => {
      notifyMutationError(error);
    });
}

function saveValue() {
  const amountMinor = parseCurrencyMinor(valueAmount.value);
  if (amountMinor === null) return;
  createValueMutation.mutate({
    effective_date: valueDate.value,
    amount_minor: amountMinor,
    source: "manual",
    notes: valueNotes.value,
    client_operation_id: crypto.randomUUID(),
  });
}

function openInvestmentStatementModal() {
  const statement = investmentStatement.value;
  investmentStatementDate.value =
    statement?.effective_date ?? localCalendarDate();
  investmentSourceAsOf.value = statement?.effective_date ?? localCalendarDate();
  investmentStatementCash.value =
    statement?.cash_balance_minor === null ||
    statement?.cash_balance_minor === undefined
      ? ""
      : String(statement.cash_balance_minor / 100);
  investmentStatementTotal.value =
    statement?.current_value_minor == null
      ? ""
      : String(statement.current_value_minor / 100);
  investmentReconciliationAttempt.value = null;
  investmentReconciliationError.value = "";
  investmentReconciliationOperationId.value = crypto.randomUUID();
  investmentHoldingRows.value = (statement?.holdings ?? []).map((holding) => ({
    ticker: holding.ticker,
    quantity: String(holding.quantity_micros / 1_000_000),
    price: String(holding.price_minor / 100),
    averageBasis:
      holding.average_basis_minor === null
        ? ""
        : String(holding.average_basis_minor / 100),
    value: String(holding.value_minor / 100),
  }));
  showInvestmentStatementModal.value = true;
}

function addInvestmentHoldingRow() {
  investmentHoldingRows.value.push({
    ticker: "",
    quantity: "",
    price: "",
    averageBasis: "",
    value: "",
  });
}

function removeInvestmentHoldingRow(index: number) {
  investmentHoldingRows.value.splice(index, 1);
}

function openInvestmentTransferModal(direction: "CONTRIBUTION" | "WITHDRAWAL") {
  investmentTransferDirection.value = direction;
  investmentTransferDate.value = new Date().toISOString().slice(0, 10);
  investmentTransferDestinationDate.value = investmentTransferDate.value;
  investmentTransferBudgetAccountId.value =
    budgetAccountOptions.value[0]?.value ?? "";
  investmentTransferAmount.value = "";
  investmentTransferMemo.value =
    direction === "CONTRIBUTION"
      ? "Investment contribution"
      : "Investment withdrawal";
  investmentTransferStatus.value = "CLEARED";
  investmentTransferDestinationStatus.value = "CLEARED";
  investmentTransferOperationId.value = crypto.randomUUID();
  showInvestmentTransferModal.value = true;
}

function saveInvestmentTransfer() {
  const amount = parseCurrencyMinor(investmentTransferAmount.value);
  if (amount === null || !investmentTransferBudgetAccountId.value) return;
  investmentTransferMutation.mutate({
    direction: investmentTransferDirection.value,
    client_operation_id: investmentTransferOperationId.value,
    source_account_id:
      investmentTransferDirection.value === "CONTRIBUTION"
        ? investmentTransferBudgetAccountId.value
        : accountId.value,
    source_posted_date: investmentTransferDate.value,
    source_status: investmentTransferStatus.value,
    destination_account_id:
      investmentTransferDirection.value === "CONTRIBUTION"
        ? accountId.value
        : investmentTransferBudgetAccountId.value,
    destination_posted_date: investmentTransferDestinationDate.value,
    destination_status: investmentTransferDestinationStatus.value,
    amount_minor: amount,
    memo: investmentTransferMemo.value,
  });
}

const investmentTransferCanSave = computed(
  () =>
    parseCurrencyMinor(investmentTransferAmount.value) !== null &&
    investmentTransferBudgetAccountId.value.length > 0 &&
    (investmentTransferDirection.value === "WITHDRAWAL" ||
      linkedContributionCategoryId.value.length > 0),
);

function openCreditCardPaymentModal() {
  creditCardPaymentSourceAccountId.value =
    budgetAccountOptions.value[0]?.value ?? "";
  creditCardPaymentSourceDate.value = new Date().toISOString().slice(0, 10);
  creditCardPaymentDestinationDate.value = creditCardPaymentSourceDate.value;
  creditCardPaymentSourceStatus.value = "CLEARED";
  creditCardPaymentDestinationStatus.value = "CLEARED";
  creditCardPaymentAmount.value = "";
  creditCardPaymentMemo.value = "Credit-card payment";
  creditCardPaymentOperationId.value = crypto.randomUUID();
  showCreditCardPaymentModal.value = true;
}

function saveCreditCardPayment() {
  const amount = parseCurrencyMinor(creditCardPaymentAmount.value);
  if (amount === null || !creditCardPaymentSourceAccountId.value) return;
  creditCardPaymentMutation.mutate({
    client_operation_id: creditCardPaymentOperationId.value,
    source_account_id: creditCardPaymentSourceAccountId.value,
    source_posted_date: creditCardPaymentSourceDate.value,
    source_status: creditCardPaymentSourceStatus.value,
    destination_account_id: accountId.value,
    destination_posted_date: creditCardPaymentDestinationDate.value,
    destination_status: creditCardPaymentDestinationStatus.value,
    amount_minor: amount,
    memo: creditCardPaymentMemo.value,
  });
}

function openLoanPaymentModal() {
  loanPaymentDate.value = new Date().toISOString().slice(0, 10);
  loanPaymentBudgetAccountId.value = budgetAccountOptions.value[0]?.value ?? "";
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
    status: "CLEARED",
    memo: loanPaymentMemo.value,
  });
}

function openLoanStatementModal() {
  const snapshot = latestLoanSnapshot.value;
  loanStatementDate.value = snapshot?.effective_date ?? localCalendarDate();
  loanPrincipal.value = snapshot
    ? String(snapshot.principal_balance_minor / 100)
    : "";
  loanAccruedInterest.value =
    snapshot?.accrued_interest_minor == null
      ? ""
      : String(snapshot.accrued_interest_minor / 100);
  loanEscrow.value =
    snapshot?.escrow_balance_minor == null
      ? ""
      : String(snapshot.escrow_balance_minor / 100);
  loanUnapplied.value =
    snapshot?.unapplied_credit_minor == null
      ? ""
      : String(snapshot.unapplied_credit_minor / 100);
  loanYtdPrincipal.value =
    snapshot?.ytd_principal_paid_minor == null
      ? ""
      : String(snapshot.ytd_principal_paid_minor / 100);
  loanYtdInterest.value =
    snapshot?.ytd_interest_paid_minor == null
      ? ""
      : String(snapshot.ytd_interest_paid_minor / 100);
  showLoanAdvancedFields.value = false;
  loanReconciliationError.value = "";
  loanMismatchNeedsCorrection.value = false;
  showLoanStatementModal.value = true;
}

function saveLoanStatement() {
  loanStatementMutation.mutate(loanReconciliationPayload());
}

const investmentSourceTotalFromParts = computed(() => {
  const cash = parseCurrencyMinor(investmentStatementCash.value);
  if (cash === null) return null;
  const values = investmentHoldingRows.value.map((holding) =>
    parseCurrencyMinor(holding.value),
  );
  if (values.some((value) => value === null)) return null;
  return cash + values.reduce<number>((sum, value) => sum + (value ?? 0), 0);
});

const investmentStatementCanSave = computed(() => {
  const declaredTotal = parseCurrencyMinor(investmentStatementTotal.value);
  if (
    declaredTotal === null ||
    declaredTotal !== investmentSourceTotalFromParts.value
  ) {
    return false;
  }
  return investmentHoldingRows.value.every(
    (holding) =>
      holding.ticker.trim().length > 0 &&
      investmentHoldingRows.value.filter(
        (candidate) =>
          candidate.ticker.trim().toUpperCase() ===
          holding.ticker.trim().toUpperCase(),
      ).length === 1 &&
      holding.quantity.trim().length > 0 &&
      Number.isFinite(Number(holding.quantity)) &&
      Number(holding.quantity) >= 0 &&
      (parseCurrencyMinor(holding.price) ?? 0) > 0 &&
      parseCurrencyMinor(holding.averageBasis) !== null &&
      parseCurrencyMinor(holding.value) !== null,
  );
});
const investmentSourceTotalError = computed(() => {
  const declared = parseCurrencyMinor(investmentStatementTotal.value);
  const derived = investmentSourceTotalFromParts.value;
  if (declared === null || derived === null || declared === derived) return "";
  return `Cash plus reported position values total ${formatCurrency(derived)}; the source total is ${formatCurrency(declared)}.`;
});

function handleInvestmentSubmit() {
  const attempt = investmentReconciliationAttempt.value;
  if (!attempt) {
    investmentAttemptMutation.mutate();
    return;
  }
  if (attempt.certification_allowed) {
    investmentApplyMutation.mutate();
    return;
  }
  showInvestmentStatementModal.value = false;
  actionMessage.value =
    "Statement differences need investigation in Holdings summary and normal account activity. No holdings were changed.";
}

function handleCommitEdit(
  id: string,
  payload: TransactionPayload,
  complete: (
    result:
      | { success: true }
      | { cancelled: true }
      | { success: false; message: string },
  ) => void,
) {
  const transaction = transactions.value.find(
    (item) => item.transaction_id === id,
  );
  if (!transaction) {
    complete({
      success: false,
      message: "This transaction is no longer available.",
    });
    return;
  }
  const previous: TransactionPayload = {
    date: transaction.date,
    account_id: transaction.account_id,
    amount_minor: transaction.amount_minor,
    category_id: transaction.category_id,
    system_category: transaction.system_category,
    status: transaction.status,
    memo: transaction.memo,
  };
  updateTransactionMutation.mutate(
    { id, payload, expectedVersion: transaction.version },
    {
      onSuccess: (result) => {
        complete({ success: true });
        notifyVersionedMutationSuccess(
          "Transaction updated",
          "Transaction edit undone",
          {
            key: `transaction:${id}`,
            version: result.version,
            run: async (expectedVersion) => {
              const restored = await updateTransaction(
                id,
                previous,
                expectedVersion,
                { acknowledgeReconciledHistoryChange: true },
              );
              invalidateAccountDetailQueries();
              if (investigatingReconciliation.value) {
                persistentEditsDuringAttempt.value = true;
                await refreshReconciliationAfterMutation();
              }
              return restored.version;
            },
          },
        );
      },
      onError: (error) => {
        if (
          error instanceof ApiError &&
          error.code === "reconciled_history_change_requires_confirmation"
        ) {
          notifyReconciledHistoryConfirmation(
            async () => {
              const result = await updateTransaction(
                id,
                payload,
                transaction.version,
                { acknowledgeReconciledHistoryChange: true },
              );
              complete({ success: true });
              transactionMutationError.value = "";
              invalidateAccountDetailQueries();
              if (investigatingReconciliation.value) {
                persistentEditsDuringAttempt.value = true;
                await refreshReconciliationAfterMutation();
              }
              notifyVersionedMutationSuccess(
                "Transaction updated",
                "Transaction edit undone",
                {
                  key: `transaction:${id}`,
                  version: result.version,
                  run: async (expectedVersion) => {
                    const restored = await updateTransaction(
                      id,
                      previous,
                      expectedVersion,
                      { acknowledgeReconciledHistoryChange: true },
                    );
                    invalidateAccountDetailQueries();
                    return restored.version;
                  },
                },
              );
            },
            () => complete({ cancelled: true }),
          );
          return;
        }
        complete({ success: false, message: mutationErrorMessage(error) });
      },
    },
  );
}

function handleRemoveTransaction(
  transaction: Transaction,
  complete: (
    result:
      | { success: true }
      | { cancelled: true }
      | { success: false; message: string },
  ) => void,
) {
  deleteTransactionMutation.mutate(
    {
      id: transaction.transaction_id,
      expectedVersion: transaction.version,
    },
    {
      onSuccess: () => {
        complete({ success: true });
        notifyVersionedMutationSuccess(
          "Transaction removed",
          "Transaction removal undone",
          {
            key: `transaction:${transaction.transaction_id}`,
            version: transaction.version,
            run: async (expectedVersion) => {
              const restored = await restoreTransaction(
                transaction.transaction_id,
                expectedVersion,
              );
              invalidateAccountDetailQueries();
              if (investigatingReconciliation.value) {
                persistentEditsDuringAttempt.value = true;
                await refreshReconciliationAfterMutation();
              }
              return restored.version;
            },
          },
        );
      },
      onError: (error) => {
        if (
          error instanceof ApiError &&
          error.code === "reconciled_history_change_requires_confirmation"
        ) {
          notifyReconciledHistoryConfirmation(
            async () => {
              await deleteTransaction(
                transaction.transaction_id,
                transaction.version,
                { acknowledgeReconciledHistoryChange: true },
              );
              complete({ success: true });
              invalidateAccountDetailQueries();
              if (investigatingReconciliation.value) {
                persistentEditsDuringAttempt.value = true;
                await refreshReconciliationAfterMutation();
              }
              notifyVersionedMutationSuccess(
                "Transaction removed",
                "Transaction removal undone",
                {
                  key: `transaction:${transaction.transaction_id}`,
                  version: transaction.version,
                  run: async (expectedVersion) => {
                    const restored = await restoreTransaction(
                      transaction.transaction_id,
                      expectedVersion,
                    );
                    invalidateAccountDetailQueries();
                    return restored.version;
                  },
                },
              );
            },
            () => complete({ cancelled: true }),
          );
          return;
        }
        complete({ success: false, message: mutationErrorMessage(error) });
      },
    },
  );
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
  configurationCategoryId.value = isInvestmentAccount.value
    ? linkedContributionCategoryId.value
    : isLoanAccount.value
      ? linkedLoanCategoryId.value
      : "";
  configurationRatePercent.value = account.value.loan_rate_minor
    ? String(account.value.loan_rate_minor / 100)
    : "";
  configurationRateType.value = account.value.loan_rate_type ?? "FIXED";
  configurationScheduledPayment.value =
    account.value.loan_scheduled_principal_interest_minor == null
      ? ""
      : String(account.value.loan_scheduled_principal_interest_minor / 100);
  configurationPaymentFrequency.value =
    account.value.loan_payment_frequency ?? "MONTHLY";
  configurationNextPaymentDate.value =
    account.value.loan_next_payment_date ?? "";
  configurationMaturityDate.value = account.value.loan_maturity_date ?? "";
  configurationRemainingTermMonths.value =
    account.value.loan_remaining_term_months == null
      ? ""
      : String(account.value.loan_remaining_term_months);
  configurationExtraPrincipal.value =
    account.value.loan_recurring_extra_principal_minor == null
      ? ""
      : String(account.value.loan_recurring_extra_principal_minor / 100);
  showConfigurationModal.value = true;
}

function saveConfiguration() {
  if (!account.value) return;
  const linkBehavior = isInvestmentAccount.value
    ? "INVESTMENT_CONTRIBUTION"
    : isLoanAccount.value
      ? "LOAN_PAYMENT"
      : null;
  const currentLinkedCategoryId = isInvestmentAccount.value
    ? linkedContributionCategoryId.value
    : linkedLoanCategoryId.value;
  const rateMinor = parsePercentMinor(configurationRatePercent.value);
  const scheduledPaymentMinor = parseCurrencyMinor(
    configurationScheduledPayment.value,
  );
  const extraPrincipalMinor = parseCurrencyMinor(
    configurationExtraPrincipal.value,
  );
  updateAccountMutation.mutate({
    id: account.value.account_id,
    payload: {
      name: configurationName.value,
      institution: configurationInstitution.value || null,
      account_number_last4: configurationLast4.value || null,
      ...(isLoanAccount.value
        ? {
            ...(rateMinor === null ? {} : { rate_minor: rateMinor }),
            rate_type: configurationRateType.value,
            ...(scheduledPaymentMinor === null
              ? {}
              : { scheduled_principal_interest_minor: scheduledPaymentMinor }),
            payment_frequency: configurationPaymentFrequency.value,
            ...(configurationNextPaymentDate.value
              ? { next_payment_date: configurationNextPaymentDate.value }
              : {}),
            ...(configurationMaturityDate.value
              ? { maturity_date: configurationMaturityDate.value }
              : {}),
            ...(configurationRemainingTermMonths.value
              ? {
                  remaining_term_months: Number(
                    configurationRemainingTermMonths.value,
                  ),
                }
              : {}),
            ...(extraPrincipalMinor === null
              ? {}
              : { recurring_extra_principal_minor: extraPrincipalMinor }),
          }
        : {}),
    },
    ...(linkBehavior &&
    configurationCategoryId.value &&
    configurationCategoryId.value !== currentLinkedCategoryId
      ? {
          linkChange: {
            action: "set" as const,
            payload: {
              category_id: configurationCategoryId.value,
              link_behavior: linkBehavior,
              effective_date: currentDate,
            },
          },
        }
      : {}),
  });
}

function retireAccount() {
  if (!account.value) return;
  updateAccountMutation.mutate({
    id: account.value.account_id,
    payload: { is_active: false, is_hidden: true },
  });
}

function openCutoverModal() {
  if (!account.value) return;
  const latestValuation = accountCurrentValue.value ?? 0;
  const name = cleanAccountName(account.value.name) ?? account.value.name;
  cutoverDate.value = new Date().toISOString().slice(0, 10);
  cutoverOperationId.value = crypto.randomUUID();
  cutoverFinalTrackingValue.value = "";
  cutoverSuccessors.value = [
    newCutoverSuccessor(String(latestValuation / 100), `${name} (Upgraded)`),
  ];
  cutoverRepresentationConfirmed.value = true;
  showCutoverModal.value = true;
}

function addCutoverSuccessor() {
  cutoverSuccessors.value.push(newCutoverSuccessor());
}

function removeCutoverSuccessor(index: number) {
  cutoverSuccessors.value.splice(index, 1);
}

function addCutoverHolding(successor: CutoverSuccessorDraft) {
  successor.holdings.push({
    ticker: "",
    quantity: "",
    price: "",
    averageBasis: "",
  });
}

function removeCutoverHolding(successor: CutoverSuccessorDraft, index: number) {
  successor.holdings.splice(index, 1);
}

function handleCutoverSubmit() {
  if (!cutoverCanSave.value || accountCurrentValue.value === null) return;
  const successors: TrackingCutoverSuccessor[] = cutoverSuccessors.value.map(
    (successor) => {
      const institution = successor.institution.trim() || undefined;
      if (successor.accountClass === "INVESTMENT") {
        return {
          account_class: "INVESTMENT",
          name: successor.name.trim(),
          ...(institution ? { institution } : {}),
          ...(successor.categoryId
            ? { contribution_category_id: successor.categoryId }
            : {}),
          cash_balance_minor: parseCurrencyMinor(successor.openingValue) ?? 0,
          holdings: successor.holdings.map((holding) => ({
            ticker: holding.ticker.trim().toUpperCase(),
            quantity_micros: Math.round(Number(holding.quantity) * 1_000_000),
            price_minor: parseCurrencyMinor(holding.price) ?? 0,
            average_basis_minor: parseCurrencyMinor(holding.averageBasis) ?? 0,
          })),
        };
      }
      if (successor.accountClass === "LOAN") {
        const accruedInterest = parseCurrencyMinor(successor.accruedInterest);
        const unappliedCredit = parseCurrencyMinor(successor.unappliedCredit);
        return {
          account_class: "LOAN",
          name: successor.name.trim(),
          ...(institution ? { institution } : {}),
          payment_category_id: successor.categoryId,
          principal_balance_minor:
            parseCurrencyMinor(successor.openingValue) ?? 0,
          escrow_balance_minor: parseCurrencyMinor(successor.escrow) ?? 0,
          ...(accruedInterest === null
            ? {}
            : { accrued_interest_minor: accruedInterest }),
          ...(unappliedCredit === null
            ? {}
            : { unapplied_credit_minor: unappliedCredit }),
        };
      }
      return {
        account_class: "TANGIBLE_ASSET",
        name: successor.name.trim(),
        ...(institution ? { institution } : {}),
        opening_value_minor: parseCurrencyMinor(successor.openingValue) ?? 0,
      };
    },
  );
  cutoverMutation.mutate({
    operation_id: cutoverOperationId.value,
    cutover_date: cutoverDate.value,
    expected_predecessor_value_minor: accountCurrentValue.value,
    final_predecessor_value_minor:
      parseCurrencyMinor(cutoverFinalTrackingValue.value) ?? 0,
    successors,
  });
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
  const normalized = value.replace(/[$,]/g, "").trim();
  if (!normalized) return null;
  const amount = Number(normalized);
  if (!Number.isFinite(amount) || amount < 0) return null;
  return Math.round(amount * 100);
}

function parseSourceBalanceMinor(value: string): number | null {
  const amount = Number(value.replace(/[$,]/g, "").trim());
  if (!Number.isFinite(amount)) return null;
  return Math.round(amount * 100);
}

function parsePercentMinor(value: string): number | null {
  const normalized = value.replace(/[%,$]/g, "").trim();
  if (!normalized) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? Math.round(parsed * 100) : null;
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
  <div
    class="account-detail-page"
    :class="{ 'account-detail-page--budget': isBudgetAccount }"
    data-cy="account-detail-page"
  >
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
              Reconcile
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
              :disabled="loanSnapshotsLoading"
              @click="openLoanStatementModal"
            >
              Reconcile
            </Button>
            <Button
              v-if="isInvestmentAccount"
              data-cy="account-detail-contribute"
              @click="openInvestmentTransferModal('CONTRIBUTION')"
            >
              Contribute
            </Button>
            <Button
              v-if="isCreditCardAccount"
              data-cy="account-detail-pay"
              @click="openCreditCardPaymentModal"
            >
              Pay
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
              Reconcile
            </Button>
            <Button
              v-if="isBudgetAccount && !investigatingReconciliation"
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

        <section
          class="account-detail-page__section account-detail-page__reconciliation-history"
          data-cy="reconciliation-history-section"
          aria-labelledby="reconciliation-history-title"
        >
          <div class="account-detail-page__section-header">
            <h2
              id="reconciliation-history-title"
              class="account-detail-page__section-title"
            >
              Reconciliation history
            </h2>
            <StateBadge
              v-if="reconciliationHistory?.items.some((item) => !item.undone)"
              variant="positive"
              size="sm"
              >On record</StateBadge
            >
            <StateBadge v-else variant="warning" size="sm"
              >Not reconciled</StateBadge
            >
          </div>
          <p
            v-if="reconciliationHistoryLoading"
            class="account-detail-page__history-state"
            role="status"
          >
            Loading reconciliation history…
          </p>
          <p
            v-else-if="reconciliationHistoryError"
            class="account-detail-page__history-state"
            role="alert"
          >
            Reconciliation history could not be loaded.
          </p>
          <template v-else-if="reconciliationHistory?.items.length">
            <p
              v-if="reconciliationAttention?.changes_since"
              class="account-detail-page__history-state"
              data-cy="reconciliation-attention"
            >
              {{ reconciliationAttention.changes_since }} changes since last
              reconciliation
              <template v-if="reconciliationAttention.carried_pending">
                · {{ reconciliationAttention.carried_pending }} carried pending
              </template>
            </p>
            <p
              v-if="reconciliationAttention?.reconciled_history_changed"
              class="account-detail-page__history-warning"
              role="status"
              data-cy="reconciled-history-warning"
            >
              Historical transaction records changed after reconciliation. Those
              edits are already saved and are not reverted by Undo.
            </p>
            <div
              v-for="item in reconciliationHistory.items"
              :key="item.reconciliation_id"
              class="account-detail-page__history-row"
              data-cy="reconciliation-history-row"
            >
              <div class="account-detail-page__history-copy">
                <strong>{{
                  reconciliationEvidenceSummary(item.reconciliation_id)
                }}</strong>
                <span v-if="item.undone"
                  >Undone · canonical changes remain in place</span
                >
                <span>
                  Source as of
                  {{
                    formatReconciliationDate(
                      reconciliationCommitById.get(item.reconciliation_id)
                        ?.source_as_of ?? item.committed_at,
                    )
                  }}
                  · Committed
                  {{ formatReconciliationDate(item.committed_at) }}
                </span>
              </div>
              <Button
                v-if="
                  latestUndoableReconciliation?.reconciliation_id ===
                  item.reconciliation_id
                "
                variant="tertiary"
                data-cy="undo-last-reconciliation"
                @click="showUndoReconciliationConfirmation = true"
              >
                Undo last reconciliation
              </Button>
            </div>
          </template>
          <p
            v-else
            class="account-detail-page__history-state"
            data-cy="never-reconciled"
          >
            Never reconciled
          </p>
        </section>

        <div
          v-if="investigatingReconciliation && budgetAttempt"
          class="account-detail-page__reconciliation-actions"
          data-cy="active-reconciliation-banner"
          aria-label="Active reconciliation controls"
        >
          <Button variant="tertiary" @click="editSourceBalances"
            >Edit source balances</Button
          >
          <Button variant="tertiary" @click="exitReconciliation"
            >Exit reconciliation</Button
          >
          <Button
            v-if="certificationAllowed"
            @click="budgetApplyMutation.mutate()"
            >Reconcile account</Button
          >
        </div>

        <section
          class="account-detail-page__budget-entry"
          aria-label="Add transaction or transfer"
        >
          <TransactionEntryForm
            ref="accountEntryForm"
            :accounts="accounts ?? []"
            :categories="categories"
            :default-account-id="accountId"
            @submit="handleAccountEntry"
          />
        </section>

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
          This tracking account was imported from Aspire Budgeting during
          net-worth migration.
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
                    data-cy="snapshot-history-row"
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
                    data-cy="loan-payment-row"
                  >
                    <span class="account-detail-page__snapshot-td"
                      >{{ payment.date }} · {{ payment.account_name }} ·
                      {{ payment.memo }} ·
                      {{
                        payment.status === "CLEARED" ? "Cleared" : "Pending"
                      }}</span
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
                  Lender actual and balance-derived
                </h2>
                <KeyValueList
                  :items="[
                    {
                      label: 'Principal balance',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.principal_balance_minor,
                      ),
                    },
                    {
                      label: 'Accrued interest',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.accrued_interest_minor,
                      ),
                    },
                    {
                      label: 'Principal reduction',
                      value: latestLoanSnapshot
                        ? formatCurrency(
                            latestLoanSnapshot.principal_reduction_minor,
                          )
                        : 'Awaiting statement',
                    },
                    {
                      label: 'YTD principal paid',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.ytd_principal_paid_minor,
                      ),
                    },
                    {
                      label: 'YTD interest paid',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.ytd_interest_paid_minor,
                      ),
                    },
                    {
                      label: 'Unknown non-principal',
                      value: latestLoanSnapshot
                        ? formatCurrency(
                            latestLoanSnapshot.unknown_nonprincipal_minor,
                          )
                        : 'Awaiting statement',
                    },
                    {
                      label: 'Unapplied credit',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.unapplied_credit_minor,
                      ),
                    },
                  ]"
                />
              </section>
              <section
                class="account-detail-page__section account-detail-page__summary"
                data-cy="loan-escrow-section"
              >
                <h2 class="account-detail-page__section-title">
                  Restricted escrow asset
                </h2>
                <KeyValueList
                  :items="[
                    {
                      label: 'Escrow balance',
                      value: formatOptionalCurrency(
                        latestLoanSnapshot?.escrow_balance_minor,
                      ),
                    },
                  ]"
                />
              </section>
              <section
                class="account-detail-page__section account-detail-page__summary"
                data-cy="loan-estimate-section"
              >
                <h2 class="account-detail-page__section-title">
                  Estimated amortization
                </h2>
                <KeyValueList
                  v-if="loanProjection?.available"
                  :items="[
                    {
                      label: 'Estimated interest accrued',
                      value: formatOptionalCurrency(
                        loanProjection.estimated_accrued_interest_minor,
                      ),
                    },
                    {
                      label: 'Projected payoff date',
                      value:
                        loanProjection.projected_payoff_date ??
                        'Beyond configured horizon',
                    },
                    {
                      label: 'Projected remaining interest',
                      value: formatOptionalCurrency(
                        loanProjection.projected_total_interest_minor,
                      ),
                    },
                    {
                      label: 'Rate assumption',
                      value: loanProjection.rate_assumption ?? '—',
                    },
                  ]"
                />
                <template v-if="loanProjection?.available">
                  <h3 class="account-detail-page__section-title">
                    Next 12 estimated payments
                  </h3>
                  <TableShell
                    :columns="loanProjectionColumns"
                    :rows="loanProjectionRows"
                    empty-text="No projected payments."
                  />
                </template>
                <p v-else class="account-detail-page__config-note">
                  {{
                    loanProjection?.reason ??
                    `Add ${loanProjection?.missing.join(", ") || "loan terms"} in account configuration to generate an estimate.`
                  }}
                </p>
              </section>
            </template>

            <template v-else>
              <section
                v-if="isBudgetAccount && investigatingReconciliation"
                class="account-detail-page__investigation"
                data-cy="reconciliation-investigation"
              >
                <div class="account-detail-page__investigation-heading">
                  <div>
                    <h2>Review differences</h2>
                    <p>
                      Changes are saved to the account ledger as you make them.
                    </p>
                  </div>
                  <div role="group" aria-label="Transaction scope">
                    <Button
                      :variant="
                        showAllReconciliationTransactions
                          ? 'tertiary'
                          : 'secondary'
                      "
                      @click="showAllReconciliationTransactions = false"
                      >Changes since last reconciliation</Button
                    >
                    <Button
                      :variant="
                        showAllReconciliationTransactions
                          ? 'secondary'
                          : 'tertiary'
                      "
                      @click="showAllReconciliationTransactions = true"
                      >All transactions</Button
                    >
                  </div>
                </div>
              </section>
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
                  <p v-if="transactionMutationError" role="alert">
                    {{ transactionMutationError }}
                  </p>
                  <div
                    v-if="investigatingReconciliation && isBudgetAccount"
                    class="account-detail-page__changes-note"
                  >
                    {{
                      showAllReconciliationTransactions
                        ? "All account transactions"
                        : `${workingSetItems.filter((item) => item.classification !== "CARRIED_PENDING").length} changes since last reconciliation`
                    }}
                  </div>
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
                    :transactions="
                      investigatingReconciliation && isBudgetAccount
                        ? investigationTransactions
                        : transactions
                    "
                    :accounts="accounts ?? []"
                    :categories="categories"
                    :total-count="
                      transactionTotal +
                      (investigatingReconciliation && isBudgetAccount
                        ? removedReconciliationTransactions.length
                        : 0)
                    "
                    :has-more="hasNextPage"
                    :loading-more="isFetchingNextPage"
                    :show-account-column="false"
                    :show-transfer-provenance="isInvestmentAccount"
                    :show-running-balance="true"
                    :reconciliation-changes="
                      investigatingReconciliation && isBudgetAccount
                        ? reconciliationChanges
                        : {}
                    "
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
                v-if="isBudgetAccount && !investigatingReconciliation"
                class="account-detail-page__section account-detail-page__summary"
                data-cy="summary-section"
              >
                <h2 class="account-detail-page__section-title">
                  Summary & notes
                </h2>
                <KeyValueList :items="summaryDetails" />
                <h3 class="account-detail-page__section-title">
                  Account details
                </h3>
                <KeyValueList :items="accountDetails" />
                <Button variant="tertiary" @click="openConfigurationModal"
                  >Edit configuration</Button
                >
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
                    <span class="account-detail-page__snapshot-td">
                      {{ holding.ticker }}
                      <span class="account-detail-page__summary-sub">
                        Basis {{ formatCurrency(holding.cost_basis_minor) }} ·
                        Gain {{ formatCurrency(holding.unrealized_gain_minor) }}
                      </span>
                    </span>
                    <span
                      class="account-detail-page__snapshot-td account-detail-page__snapshot-td--end"
                    >
                      {{ formatCurrency(holding.value_minor) }}
                    </span>
                  </div>
                </div>
                <p v-else class="account-detail-page__empty">
                  {{
                    investmentStatement?.effective_date
                      ? "No holdings in latest statement."
                      : "No statement recorded."
                  }}
                </p>
              </section>
            </template>
          </div>

          <aside v-if="!isBudgetAccount" class="account-detail-page__sidebar">
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
          </aside>
        </div>

        <FormModal
          :visible="showReconciliationModal"
          title="Reconcile account"
          :submit-text="budgetReconciliationSubmitText"
          :submit-disabled="!budgetAttempt && !sourceEntryReady"
          :loading="
            budgetAttemptMutation.isPending.value ||
            budgetApplyMutation.isPending.value
          "
          @submit="
            budgetAttempt
              ? certificationAllowed
                ? budgetApplyMutation.mutate()
                : reviewReconciliationDifferences()
              : previewBudgetBalances()
          "
          @cancel="cancelReconciliationEntry"
          @close="cancelReconciliationEntry"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="sourceAsOfDate"
              label="Source as of"
              name="reconciliation-cutoff"
              :max="currentDate"
            />
            <p class="account-detail-page__config-note">
              Enter any two source balances. dojo derives the third; Cleared and
              Pending must both match before this account can be reconciled.
            </p>
            <CurrencyField
              :model-value="sourceInputValue('cleared')"
              label="Cleared"
              name="source-cleared"
              :disabled="sourceInputDisabled('cleared')"
              @update:model-value="
                sourceCleared = $event;
                budgetAttempt = null;
              "
            />
            <CurrencyField
              :model-value="sourceInputValue('pending')"
              label="Pending"
              name="source-pending"
              :disabled="sourceInputDisabled('pending')"
              @update:model-value="
                sourcePending = $event;
                budgetAttempt = null;
              "
            />
            <CurrencyField
              :model-value="sourceInputValue('actual')"
              label="Actual"
              name="source-actual"
              :disabled="sourceInputDisabled('actual')"
              @update:model-value="
                sourceActual = $event;
                budgetAttempt = null;
              "
            />
            <p
              v-if="derivedSourceBalance"
              class="account-detail-page__config-note"
              data-cy="derived-balance"
            >
              {{ derivedSourceBalance.key }} is derived from the other two
              source balances.
            </p>
            <div
              v-if="budgetAttempt"
              class="account-detail-page__reconciliation-proof"
              data-cy="budget-reconciliation-proof"
            >
              <strong>{{
                certificationAllowed ? "Balances match" : "Differences found"
              }}</strong>
              <span
                >Cleared Δ
                {{
                  formatCurrency(budgetAttempt.deltas.cleared_delta_minor)
                }}</span
              >
              <span
                >Pending Δ
                {{
                  formatCurrency(budgetAttempt.deltas.pending_delta_minor)
                }}</span
              >
              <span
                >Actual Δ
                {{
                  formatCurrency(budgetAttempt.deltas.actual_delta_minor)
                }}</span
              >
            </div>
            <p
              v-if="reconciliationMutationError"
              class="account-detail-page__config-note"
              role="alert"
            >
              {{ reconciliationMutationError }}
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showExitWarning"
          title="Exit reconciliation?"
          submit-text="Exit reconciliation"
          @submit="confirmExitReconciliation"
          @cancel="showExitWarning = false"
          @close="showExitWarning = false"
        >
          <p>
            Your transaction edits have already been saved. Exiting will leave
            no reconciliation recorded for this account.
          </p>
        </FormModal>

        <FormModal
          :visible="showUndoReconciliationConfirmation"
          title="Undo last reconciliation?"
          submit-text="Undo last reconciliation"
          @submit="confirmUndoLastReconciliation"
          @cancel="showUndoReconciliationConfirmation = false"
          @close="showUndoReconciliationConfirmation = false"
        >
          <p>
            This appends an undo record for the latest reconciliation. It does
            not revert account, transaction, or valuation changes already saved.
          </p>
        </FormModal>

        <FormModal
          :visible="showConfigurationModal"
          title="Edit account configuration"
          submit-text="Save"
          danger-text="Retire account"
          :submit-disabled="isLoanAccount && !configurationCategoryId"
          :loading="configurationSaving"
          @submit="saveConfiguration"
          @danger="retireAccount"
          @cancel="showConfigurationModal = false"
          @close="showConfigurationModal = false"
        >
          <div class="account-detail-page__config-form">
            <TextField v-model="configurationName" label="Name" name="name" />
            <InstitutionCombobox
              v-model="configurationInstitution"
              name="institution"
              :options="suggestedInstitutions"
            />
            <TextField
              v-model="configurationLast4"
              label="Account number last4"
              name="account-number-last4"
            />
            <SelectField
              v-if="isInvestmentAccount || isLoanAccount"
              v-model="configurationCategoryId"
              :label="
                isInvestmentAccount
                  ? 'Contribution category'
                  : 'Payment category'
              "
              name="configured-category"
              :options="configurableCategoryOptions"
            />
            <p class="account-detail-page__config-note">
              Account type and net-worth inclusion are not configurable here.
              Active financial entities contribute to net worth according to
              their type.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showCreditCardPaymentModal"
          title="Pay credit card"
          submit-text="Save payment"
          :submit-disabled="
            parseCurrencyMinor(creditCardPaymentAmount) === null ||
            !creditCardPaymentSourceAccountId
          "
          :loading="creditCardPaymentMutation.isPending.value"
          @submit="saveCreditCardPayment"
          @cancel="showCreditCardPaymentModal = false"
          @close="showCreditCardPaymentModal = false"
        >
          <div class="account-detail-page__config-form">
            <SelectField
              v-model="creditCardPaymentSourceAccountId"
              label="From account"
              name="credit-card-payment-source"
              :options="budgetAccountOptions"
            />
            <DatePicker
              v-model="creditCardPaymentSourceDate"
              label="Source posted date"
              name="credit-card-payment-source-date"
            />
            <SelectField
              v-model="creditCardPaymentSourceStatus"
              label="Source status"
              name="credit-card-payment-source-status"
              :options="[
                { value: 'CLEARED', label: 'Cleared' },
                { value: 'PENDING', label: 'Pending' },
              ]"
            />
            <DatePicker
              v-model="creditCardPaymentDestinationDate"
              label="Card posted date"
              name="credit-card-payment-card-date"
            />
            <SelectField
              v-model="creditCardPaymentDestinationStatus"
              label="Card status"
              name="credit-card-payment-card-status"
              :options="[
                { value: 'CLEARED', label: 'Cleared' },
                { value: 'PENDING', label: 'Pending' },
              ]"
            />
            <CurrencyField
              v-model="creditCardPaymentAmount"
              label="Amount"
              name="credit-card-payment-amount"
            />
            <TextField
              v-model="creditCardPaymentMemo"
              label="Memo"
              name="credit-card-payment-memo"
            />
            <p class="account-detail-page__cutover-info">
              The checking outflow and card payment-category reserve are equal
              and opposite. Net worth is unchanged.
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
            !linkedLoanCategoryId
          "
          :loading="loanPaymentMutation.isPending.value"
          @submit="saveLoanPayment"
          @cancel="showLoanPaymentModal = false"
          @close="showLoanPaymentModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="loanPaymentDate"
              label="Source posted date"
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
            <TextField
              v-model="loanPaymentMemo"
              label="Memo"
              name="loan-payment-memo"
            />
            <p class="account-detail-page__config-note">
              Payment category:
              {{
                selectedLoanCategory?.name ?? "Configure this account first"
              }}. Enter the cash payment only. Principal and non-principal
              amounts are derived when the lender statement is reconciled.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showLoanStatementModal"
          title="Reconcile loan"
          submit-text="Reconcile"
          :submit-disabled="
            parseCurrencyMinor(loanPrincipal) === null ||
            loanMismatchNeedsCorrection
          "
          :loading="
            loanStatementMutation.isPending.value ||
            correctLoanSnapshotMutation.isPending.value
          "
          @submit="saveLoanStatement"
          @cancel="showLoanStatementModal = false"
          @close="showLoanStatementModal = false"
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="loanStatementDate"
              label="Statement date"
              name="loan-statement-date"
              :max="currentDate"
            />
            <CurrencyField
              v-model="loanPrincipal"
              label="Principal balance"
              name="loan-principal"
            />
            <CurrencyField
              v-model="loanEscrow"
              label="Escrow balance"
              name="loan-escrow"
            />
            <Button
              variant="secondary"
              size="sm"
              @click="showLoanAdvancedFields = !showLoanAdvancedFields"
            >
              {{
                showLoanAdvancedFields
                  ? "Hide optional fields"
                  : "Show optional fields"
              }}
            </Button>
            <template v-if="showLoanAdvancedFields">
              <CurrencyField
                v-model="loanAccruedInterest"
                label="Accrued interest"
                name="loan-interest"
              />
              <CurrencyField
                v-model="loanUnapplied"
                label="Unapplied credit"
                name="loan-unapplied"
              />
              <CurrencyField
                v-model="loanYtdPrincipal"
                label="YTD principal paid"
                name="loan-ytd-principal"
              />
              <CurrencyField
                v-model="loanYtdInterest"
                label="YTD interest paid"
                name="loan-ytd-interest"
              />
            </template>
            <p class="account-detail-page__config-note">
              Only lender-provided facts are recorded. Blank optional fields
              remain unknown; enter zero only when the lender states zero.
            </p>
            <p v-if="loanReconciliationError" role="alert">
              {{ loanReconciliationError }}
            </p>
            <Button
              v-if="loanMismatchNeedsCorrection"
              variant="secondary"
              data-cy="loan-correct-canonical-snapshot"
              :loading="correctLoanSnapshotMutation.isPending.value"
              @click="correctLoanSnapshotMutation.mutate()"
            >
              Correct canonical snapshot and reconcile
            </Button>
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
              label="Source status"
              name="investment-transfer-status"
              :options="[
                { value: 'CLEARED', label: 'Cleared' },
                { value: 'PENDING', label: 'Pending' },
              ]"
            />
            <DatePicker
              v-model="investmentTransferDestinationDate"
              label="Destination posted date"
              name="investment-transfer-destination-date"
            />
            <SelectField
              v-model="investmentTransferDestinationStatus"
              label="Destination status"
              name="investment-transfer-destination-status"
              :options="[
                { value: 'CLEARED', label: 'Cleared' },
                { value: 'PENDING', label: 'Pending' },
              ]"
            />
            <TextField
              v-model="investmentTransferMemo"
              label="Memo"
              name="investment-transfer-memo"
            />
            <div class="account-detail-page__cutover-info">
              <span v-if="investmentTransferDirection === 'CONTRIBUTION'">
                {{
                  selectedContributionCategory?.name ??
                  "No category configured"
                }}:
                {{ formatCurrency(contributionPreview.available) }} available −
                {{ formatCurrency(contributionPreview.amount) }} contribution =
                {{ formatCurrency(contributionPreview.resultingAvailable) }}.
                The transfer creates two ledger legs and does not change net
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
          title="Reconcile investment account"
          :submit-text="
            !investmentReconciliationAttempt
              ? 'Compare statement'
              : investmentReconciliationAttempt.certification_allowed
                ? 'Reconcile account'
                : 'Review holdings'
          "
          :submit-disabled="!investmentStatementCanSave"
          :loading="
            investmentAttemptMutation.isPending.value ||
            investmentApplyMutation.isPending.value
          "
          @submit="handleInvestmentSubmit"
          @cancel="
            showInvestmentStatementModal = false;
            investmentReconciliationAttempt = null;
          "
          @close="
            showInvestmentStatementModal = false;
            investmentReconciliationAttempt = null;
          "
        >
          <div class="account-detail-page__config-form">
            <DatePicker
              v-model="investmentStatementDate"
              label="Statement effective date"
              name="investment-statement-date"
              :max="currentDate"
            />
            <DatePicker
              v-model="investmentSourceAsOf"
              label="Source as of"
              name="investment-source-as-of"
              :max="currentDate"
            />
            <CurrencyField
              v-model="investmentStatementCash"
              label="Cash balance"
              name="investment-statement-cash"
            />
            <CurrencyField
              v-model="investmentStatementTotal"
              label="Total account value"
              name="investment-statement-total"
            />
            <p
              v-if="investmentSourceTotalError"
              class="account-detail-page__config-note"
              role="alert"
              data-cy="investment-source-total-error"
            >
              {{ investmentSourceTotalError }}
            </p>
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
              <p
                v-if="investmentHoldingRows.length === 0"
                class="account-detail-page__config-note"
              >
                No holdings. This statement will record a cash-only investment
                account.
              </p>
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
                  v-model="holding.value"
                  label="Reported position value"
                  :name="`holding-value-${index}`"
                />
                <CurrencyField
                  v-model="holding.averageBasis"
                  label="Average cost per unit"
                  :name="`holding-basis-${index}`"
                />
                <Button
                  variant="tertiary"
                  size="sm"
                  @click="removeInvestmentHoldingRow(index)"
                >
                  Remove
                </Button>
              </div>
            </div>
            <p class="account-detail-page__config-note">
              The source total must equal cash plus reported position values.
              Price movement is shown separately and does not change structural
              holdings.
            </p>
            <div
              v-if="investmentReconciliationAttempt"
              class="account-detail-page__reconciliation-proof"
              data-cy="investment-reconciliation-proof"
            >
              <strong>
                {{
                  investmentReconciliationAttempt.certification_allowed
                    ? "Balances match"
                    : "Differences found"
                }}
              </strong>
              <span>
                {{ investmentReconciliationAttempt.diffs.length }} structural
                {{
                  investmentReconciliationAttempt.diffs.length === 1
                    ? "difference"
                    : "differences"
                }}
              </span>
              <span
                >{{ investmentReconciliationAttempt.price_only_changes.length }}
                price-only
                {{
                  investmentReconciliationAttempt.price_only_changes.length ===
                  1
                    ? "change"
                    : "changes"
                }}</span
              >
              <span
                v-if="!investmentReconciliationAttempt.certification_allowed"
              >
                No canonical holdings were changed. Investigate in Holdings
                summary before retrying.
              </span>
            </div>
            <p v-if="investmentReconciliationError" role="alert">
              {{ investmentReconciliationError }}
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showValueModal"
          title="Reconcile valuation"
          submit-text="Reconcile"
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
              :max="currentDate"
            />
            <CurrencyField
              v-model="valueAmount"
              :label="isTrackingAccount ? 'Snapshot value' : 'Valuation'"
              name="value-amount"
              data-cy="account-detail-value-amount"
            />
            <TextField v-model="valueNotes" label="Notes" name="value-notes" />
            <p class="account-detail-page__config-note">
              A changed value and its reconciliation commit are recorded
              together. Repeating the same value records new evidence only.
            </p>
          </div>
        </FormModal>

        <FormModal
          :visible="showCutoverModal"
          title="Replace tracking account"
          submit-text="Apply cutover"
          :submit-disabled="!cutoverCanSave"
          :loading="cutoverMutation.isPending.value"
          @submit="handleCutoverSubmit"
          @cancel="showCutoverModal = false"
          @close="showCutoverModal = false"
        >
          <p class="account-detail-page__cutover-description">
            We'll create one or more richer entities and retire this
            {{ cleanAccountName(account?.name) ?? account?.name }} tracking
            account effective the cutover date. This is a representation change,
            not a ledger transfer.
          </p>
          <div class="account-detail-page__cutover-form">
            <DatePicker
              v-model="cutoverDate"
              label="Cutover date"
              name="cutover-date"
              helper="Successors become current on this date"
            />
            <CurrencyField
              v-model="cutoverFinalTrackingValue"
              label="Final tracking value"
              name="cutover-final-tracking-value"
              helper="Enter the source value as of the cutover date"
            />
            <section
              v-for="(successor, successorIndex) in cutoverSuccessors"
              :key="successor.id"
              class="account-detail-page__section"
              data-cy="cutover-successor"
            >
              <div class="account-detail-page__section-header">
                <h3 class="account-detail-page__section-title">
                  Successor {{ successorIndex + 1 }}
                </h3>
                <Button
                  v-if="cutoverSuccessors.length > 1"
                  variant="tertiary"
                  size="sm"
                  @click="removeCutoverSuccessor(successorIndex)"
                >
                  Remove
                </Button>
              </div>
              <SelectField
                v-model="successor.accountClass"
                label="Entity type"
                :name="`cutover-type-${successorIndex}`"
                :options="[
                  { value: 'INVESTMENT', label: 'Investment account' },
                  { value: 'LOAN', label: 'Loan' },
                  { value: 'TANGIBLE_ASSET', label: 'Tangible asset' },
                ]"
              />
              <TextField
                v-model="successor.name"
                label="Name"
                :name="`cutover-name-${successorIndex}`"
              />
              <InstitutionCombobox
                v-model="successor.institution"
                :name="`cutover-institution-${successorIndex}`"
                :options="suggestedInstitutions"
              />
              <CurrencyField
                v-model="successor.openingValue"
                :label="
                  successor.accountClass === 'LOAN'
                    ? 'Opening principal'
                    : successor.accountClass === 'INVESTMENT'
                      ? 'Opening cash balance'
                      : 'Opening value'
                "
                :name="`cutover-opening-${successorIndex}`"
              />
              <SelectField
                v-if="successor.accountClass === 'INVESTMENT'"
                v-model="successor.categoryId"
                label="Contribution category"
                :name="`cutover-category-${successorIndex}`"
                :options="[
                  { value: '', label: 'Do not link a category yet' },
                  ...contributionCategoryOptions,
                ]"
              />
              <template v-if="successor.accountClass === 'INVESTMENT'">
                <div class="account-detail-page__section-header">
                  <h4 class="account-detail-page__section-title">
                    Opening holdings
                  </h4>
                  <Button
                    variant="secondary"
                    size="sm"
                    @click="addCutoverHolding(successor)"
                  >
                    Add holding
                  </Button>
                </div>
                <div
                  v-for="(holding, holdingIndex) in successor.holdings"
                  :key="holdingIndex"
                  class="account-detail-page__statement-holding"
                >
                  <TextField
                    v-model="holding.ticker"
                    label="Ticker"
                    :name="`cutover-ticker-${successorIndex}-${holdingIndex}`"
                  />
                  <TextField
                    v-model="holding.quantity"
                    label="Quantity"
                    :name="`cutover-quantity-${successorIndex}-${holdingIndex}`"
                    inputmode="decimal"
                  />
                  <CurrencyField
                    v-model="holding.price"
                    label="Price per unit on cutover date"
                    :name="`cutover-price-${successorIndex}-${holdingIndex}`"
                  />
                  <CurrencyField
                    v-model="holding.averageBasis"
                    label="Average cost per unit"
                    :name="`cutover-basis-${successorIndex}-${holdingIndex}`"
                  />
                  <Button
                    variant="tertiary"
                    size="sm"
                    @click="removeCutoverHolding(successor, holdingIndex)"
                  >
                    Remove
                  </Button>
                </div>
              </template>
              <template v-if="successor.accountClass === 'LOAN'">
                <SelectField
                  v-model="successor.categoryId"
                  label="Payment category"
                  :name="`cutover-category-${successorIndex}`"
                  :options="contributionCategoryOptions"
                />
                <CurrencyField
                  v-model="successor.escrow"
                  label="Opening escrow"
                  :name="`cutover-escrow-${successorIndex}`"
                />
                <CurrencyField
                  v-model="successor.accruedInterest"
                  label="Accrued interest (optional)"
                  :name="`cutover-interest-${successorIndex}`"
                />
                <CurrencyField
                  v-model="successor.unappliedCredit"
                  label="Unapplied credit (optional)"
                  :name="`cutover-unapplied-${successorIndex}`"
                />
              </template>
            </section>
            <Button variant="secondary" size="sm" @click="addCutoverSuccessor">
              Add successor
            </Button>
            <div class="account-detail-page__cutover-info">
              <div data-cy="cutover-value-reconciliation">
                <span>
                  Final tracking value:
                  {{ formatCurrency(cutoverExpectedSignedValue) }} · Successor
                  total: {{ formatCurrency(cutoverSuccessorTotal) }}
                </span>
                <span v-if="hasCutoverInvestmentSuccessor">
                  Investment breakdown: cash
                  {{ formatCurrency(cutoverInvestmentCashTotal) }} + holdings
                  {{ formatCurrency(cutoverInvestmentHoldingsTotal) }}
                </span>
                <strong>{{ cutoverDifferenceDescription }}</strong>
              </div>
            </div>
            <label class="account-detail-page__cutover-checkbox">
              <input v-model="cutoverRepresentationConfirmed" type="checkbox" />
              <span>
                This is a representation change, not a ledger transfer. No money
                moves and no transactions are posted. We're replacing a snapshot
                with successor entities whose opening values exactly reconcile
                to the final tracking value.
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
                the cutover date, as-of views use the successor entities.
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
  min-width: 0;
  background: var(--color-background);
}

.account-detail-page__main {
  min-width: 0;
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

.account-detail-page__budget-entry {
  min-width: 0;
  order: 3;
}
.account-detail-page__metrics {
  order: 2;
}
.account-detail-page__reconciliation-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-sm);
  order: 2;
}
.account-detail-page__content {
  order: 4;
}
.account-detail-page--budget .account-detail-page__content {
  grid-template-columns: minmax(0, 1fr);
}
.account-detail-page--budget .account-detail-page__left {
  grid-template-columns: minmax(0, 1fr);
}
.account-detail-page__investigation {
  display: grid;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
}
.account-detail-page__investigation p {
  color: var(--color-on-surface-muted);
}
.account-detail-page__investigation-heading,
.account-detail-page__investigation-heading > div:last-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}
.account-detail-page__investigation h2,
.account-detail-page__investigation p {
  margin: 0;
}
.account-detail-page__investigation-heading > div:first-child {
  display: grid;
  gap: var(--space-xs);
}
.account-detail-page__changes-note {
  padding: var(--space-sm) var(--space-md);
  color: var(--color-on-surface-muted);
  font: var(--text-body-sm-font-weight) var(--text-body-sm-font-size)
    var(--text-body-sm-font-family);
}
.account-detail-page__reconciliation-proof {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-xs) var(--space-md);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}
.account-detail-page__reconciliation-proof strong {
  color: var(--color-positive);
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
  min-width: 0;
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

.account-detail-page__reconciliation-history {
  padding: var(--space-lg);
}

.account-detail-page__history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--color-outline);
}

.account-detail-page__history-copy {
  display: grid;
  gap: var(--space-xs);
  min-width: 0;
  color: var(--color-on-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__history-copy span,
.account-detail-page__history-state {
  margin: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  line-height: var(--text-body-sm-line-height);
}

.account-detail-page__history-warning {
  margin: var(--space-md) 0;
  padding: var(--space-md);
  color: var(--color-warning);
  background: var(--color-warning-container);
  border: 1px solid var(--color-warning);
  border-radius: var(--radius-all);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
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

.account-detail-page__cutover-info > div {
  display: grid;
  gap: var(--space-xs);
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

@media (max-width: 600px) {
  .account-detail-page__history-row {
    align-items: flex-start;
    flex-direction: column;
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
