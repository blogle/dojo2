<script setup lang="ts">
import { computed, ref } from "vue";
import { useQuery, useMutation, useQueryClient } from "@tanstack/vue-query";

import type {
  Transaction,
  TransactionPayload,
  TransactionSystemCategory,
} from "../types";
import { formatCurrency, formatMonth } from "../utils/currency";
import {
  fetchTransactionsPage,
  type TransactionFilters,
  fetchAccounts,
  fetchCategories,
  createTransaction,
  createTransfer,
  updateTransaction,
  deleteTransaction,
  restoreTransaction,
  ApiError,
} from "../api/client";
import {
  notifyMutationSuccess,
  notifyVersionedMutationSuccess,
  notifyMutationError,
  mutationErrorMessage,
} from "../state/mutationFeedback";

import PageHeader from "../components/data/PageHeader.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import type { MetricStripItem } from "../components/data/MetricStrip.vue";
import TransactionEntryForm from "../components/transactions/TransactionEntryForm.vue";
import TransactionFilterBar from "../components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "../components/transactions/TransactionLedger.vue";

const queryClient = useQueryClient();
const entryForm = ref<InstanceType<typeof TransactionEntryForm> | null>(null);

const PAGE_SIZE = 10_000;
const QUERY_KEYS = {
  transactions: ["transactions", PAGE_SIZE] as const,
  accounts: ["accounts"] as const,
  categories: ["categories"] as const,
  budget: ["budget"] as const,
  allocations: ["allocations"] as const,
  netWorth: ["net-worth"] as const,
  categoryActivity: ["category-activity"] as const,
} as const;

const accountFilter = ref("all");
const dateFilter = ref("all");
const categoryFilter = ref("all");
const amountFilter = ref("all");
const statusFilter = ref("all");
const activityFilter = ref<"all" | "spending" | "transfers">("all");

const currentMonth = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
});

const { data: txPage } = useQuery({
  queryKey: computed(() => [
    ...QUERY_KEYS.transactions,
    accountFilter.value,
    dateFilter.value,
    categoryFilter.value,
    amountFilter.value,
    statusFilter.value,
  ]),
  queryFn: () =>
    fetchTransactionsPage(false, 0, PAGE_SIZE, transactionFilters.value),
});

const transactions = computed(() => {
  const items = txPage.value?.items ?? [];
  if (activityFilter.value === "transfers") {
    return items.filter(
      (transaction) => transaction.system_category === "TX_ACCOUNT_TRANSFER",
    );
  }
  if (activityFilter.value === "spending") {
    return items.filter(
      (transaction) => transaction.system_category !== "TX_ACCOUNT_TRANSFER",
    );
  }
  return items;
});

const { data: accounts } = useQuery({
  queryKey: QUERY_KEYS.accounts,
  queryFn: () => fetchAccounts(false),
});

const { data: categoriesResponse } = useQuery({
  queryKey: QUERY_KEYS.categories,
  queryFn: () => fetchCategories(currentMonth.value, false),
});

const categories = computed(() => categoriesResponse.value?.items ?? []);

function invalidateRelatedQueries() {
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transactions });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.accounts });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.budget });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.allocations });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.netWorth });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categories });
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.categoryActivity });
  queryClient.invalidateQueries({ queryKey: ["available-to-budget"] });
}

const createMutation = useMutation({
  mutationFn: createTransaction,
  onSuccess: (created) => {
    entryForm.value?.resetForm();
    invalidateRelatedQueries();
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
          invalidateRelatedQueries();
        },
      },
    );
  },
});

const updateMutation = useMutation({
  mutationFn: ({
    id,
    payload,
    expectedVersion,
  }: {
    id: string;
    payload: Parameters<typeof updateTransaction>[1];
    expectedVersion: string;
  }) => updateTransaction(id, payload, expectedVersion),
  onSuccess: () => invalidateRelatedQueries(),
});

const deleteMutation = useMutation({
  mutationFn: ({
    id,
    expectedVersion,
  }: {
    id: string;
    expectedVersion: string;
  }) => deleteTransaction(id, expectedVersion),
  onSuccess: () => invalidateRelatedQueries(),
});

const inflow = computed(() =>
  transactions.value
    .filter((t) => t.amount_minor > 0)
    .reduce((sum, t) => sum + t.amount_minor, 0),
);

const outflow = computed(() =>
  transactions.value
    .filter((t) => t.amount_minor < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount_minor), 0),
);

const net = computed(() => inflow.value - outflow.value);

const transactionFilters = computed<TransactionFilters>(() => ({
  ...(accountFilter.value !== "all" ? { accountId: accountFilter.value } : {}),
  ...(categoryFilter.value !== "all"
    ? { categoryId: categoryFilter.value }
    : {}),
  ...(statusFilter.value === "cleared" ? { status: "CLEARED" as const } : {}),
  ...(statusFilter.value === "pending" ? { status: "PENDING" as const } : {}),
  ...datePresetToFilter(dateFilter.value),
  ...amountPresetToFilter(amountFilter.value),
}));

const metrics = computed<MetricStripItem[]>(() => [
  {
    key: "inflow",
    label: activityFilter.value === "spending" ? "Inflow" : "Gross Inflow",
    value: formatCurrency(inflow.value),
  },
  {
    key: "outflow",
    label: activityFilter.value === "spending" ? "Outflow" : "Gross Outflow",
    value: formatCurrency(outflow.value),
  },
  {
    key: "net",
    label: activityFilter.value === "spending" ? "Net" : "Net Flow",
    value: formatCurrency(net.value),
  },
]);

function handleCommitEdit(
  id: string,
  payload: Parameters<typeof updateTransaction>[1],
  complete: (
    result: { success: true } | { success: false; message: string },
  ) => void,
) {
  const tx = transactions.value.find((t) => t.transaction_id === id);
  if (!tx) {
    complete({
      success: false,
      message: "This transaction is no longer available.",
    });
    return;
  }
  const previous: TransactionPayload = {
    date: tx.date,
    account_id: tx.account_id,
    amount_minor: tx.amount_minor,
    category_id: tx.category_id,
    system_category: tx.system_category,
    status: tx.status,
    memo: tx.memo,
  };
  updateMutation.mutate(
    { id, payload, expectedVersion: tx.version },
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
              invalidateRelatedQueries();
              return restored.version;
            },
          },
        );
      },
      onError: (error) => {
        if (error instanceof ApiError && error.status === 409) {
          invalidateRelatedQueries();
        }
        complete({ success: false, message: mutationErrorMessage(error) });
      },
    },
  );
}

function handleSubmit(
  payload:
    | {
        date: string;
        account_id: string;
        amount_minor: number;
        category_id: string | null;
        system_category: TransactionSystemCategory | null;
        status: "PENDING" | "CLEARED";
        memo: string;
      }
    | {
        kind: "transfer";
        date: string;
        from_account_id: string;
        to_account_id: string;
        amount_minor: number;
        status: "PENDING" | "CLEARED";
        memo: string;
        to_account_date: string;
        to_account_status: "PENDING" | "CLEARED";
        to_account_memo: string;
      },
) {
  if ("kind" in payload) {
    void createTransfer({
      date: payload.date,
      from_account_id: payload.from_account_id,
      to_account_id: payload.to_account_id,
      amount_minor: payload.amount_minor,
      status: payload.status,
      memo: payload.memo,
      source_date: payload.date,
      source_status: payload.status,
      source_memo: payload.memo,
      destination_date: payload.to_account_date,
      destination_status: payload.to_account_status,
      destination_memo: payload.to_account_memo,
    })
      .then(() => {
        entryForm.value?.resetForm();
        invalidateRelatedQueries();
        notifyMutationSuccess("Transfer added");
      })
      .catch(notifyMutationError);
    return;
  }
  createMutation.mutate(payload);
}

function handleRemove(
  tx: Transaction,
  complete: (
    result: { success: true } | { success: false; message: string },
  ) => void,
) {
  deleteMutation.mutate(
    { id: tx.transaction_id, expectedVersion: tx.version },
    {
      onSuccess: () => {
        complete({ success: true });
        invalidateRelatedQueries();
        notifyVersionedMutationSuccess(
          "Transaction removed",
          "Transaction removal undone",
          {
            key: `transaction:${tx.transaction_id}`,
            version: tx.version,
            run: async (expectedVersion) => {
              const restored = await restoreTransaction(
                tx.transaction_id,
                expectedVersion,
              );
              invalidateRelatedQueries();
              return restored.version;
            },
          },
        );
      },
      onError: (error) => {
        if (error instanceof ApiError && error.status === 409) {
          invalidateRelatedQueries();
        }
        complete({ success: false, message: mutationErrorMessage(error) });
      },
    },
  );
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
</script>

<template>
  <div class="transactions-page" data-cy="transactions-page-root">
    <main class="transactions-page__main">
      <PageHeader title="Transactions" />

      <div class="transactions-page__month-nav">
        <span class="transactions-page__month-icon">📅</span>
        <span class="transactions-page__month-label">
          {{ formatMonth(currentMonth) }}
        </span>
      </div>

      <MetricStrip :items="metrics" />

      <TransactionEntryForm
        :accounts="accounts ?? []"
        :categories="categories"
        @submit="handleSubmit"
      />

      <TransactionFilterBar
        :accounts="accounts ?? []"
        :categories="categories"
        :account-filter="accountFilter"
        :date-filter="dateFilter"
        :category-filter="categoryFilter"
        :amount-filter="amountFilter"
        :status-filter="statusFilter"
        :activity-filter="activityFilter"
        @update:account-filter="accountFilter = $event"
        @update:date-filter="dateFilter = $event"
        @update:category-filter="categoryFilter = $event"
        @update:amount-filter="amountFilter = $event"
        @update:status-filter="statusFilter = $event"
        @update:activity-filter="activityFilter = $event"
      />

      <TransactionLedger
        :transactions="transactions"
        :accounts="accounts ?? []"
        :categories="categories"
        :total-count="txPage?.total"
        @commit="handleCommitEdit"
        @remove="handleRemove"
      />
    </main>
  </div>
</template>

<style scoped>
.transactions-page {
  min-width: 0;
  background: var(--color-background);
}

.transactions-page__main {
  min-width: 0;
  padding: var(--space-page-block) var(--space-page-inline);
  display: grid;
  gap: var(--space-lg);
  align-content: start;
  position: relative;
}

.transactions-page__month-nav {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-all);
  background: var(--color-surface);
  width: fit-content;
}

.transactions-page__month-icon {
  font-size: 14px;
}

.transactions-page__month-label {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  color: var(--color-on-surface);
}

@media (max-width: 720px) {
  .transactions-page__main {
    padding: var(--space-md);
  }
}
</style>
