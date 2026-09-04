<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useQuery, useMutation, useQueryClient } from "@tanstack/vue-query";

import type { Transaction, TransactionPayload } from "../types";
import { formatCurrency, formatMonth } from "../utils/currency";
import {
  fetchTransactionsPage,
  type TransactionFilters,
  fetchAccounts,
  fetchCategories,
  createTransaction,
  updateTransaction,
  deleteTransaction,
  restoreTransaction,
  ApiError,
} from "../api/client";

import NavigationRail from "../components/navigation/NavigationRail.vue";
import PageHeader from "../components/data/PageHeader.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import type { MetricStripItem } from "../components/data/MetricStrip.vue";
import Button from "../components/actions/Button.vue";
import TransactionEntryForm from "../components/transactions/TransactionEntryForm.vue";
import TransactionFilterBar from "../components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "../components/transactions/TransactionLedger.vue";
import PersistentWarningBanner from "../components/feedback/PersistentWarningBanner.vue";

const queryClient = useQueryClient();
const entryForm = ref<InstanceType<typeof TransactionEntryForm> | null>(null);
const mutationError = ref("");

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

type UndoEntry =
  | {
      kind: "edit";
      id: string;
      previous: TransactionPayload;
      expectedVersion: string;
    }
  | { kind: "remove"; snapshot: Transaction };

const undoStack = ref<UndoEntry[]>([]);
const showUndoToast = ref(false);
const lastRemovedSnapshot = ref<Transaction | null>(null);
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
}

const createMutation = useMutation({
  mutationFn: createTransaction,
  onMutate: () => (mutationError.value = ""),
  onSuccess: () => {
    entryForm.value?.resetForm();
    invalidateRelatedQueries();
  },
  onError: (error) => handleMutationError(error),
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
  onMutate: () => (mutationError.value = ""),
  onSuccess: () => invalidateRelatedQueries(),
  onError: (error) => handleMutationError(error),
});

const deleteMutation = useMutation({
  mutationFn: ({
    id,
    expectedVersion,
  }: {
    id: string;
    expectedVersion: string;
  }) => deleteTransaction(id, expectedVersion),
  onMutate: () => (mutationError.value = ""),
  onSuccess: () => invalidateRelatedQueries(),
  onError: (error) => handleMutationError(error),
});

const restoreMutation = useMutation({
  mutationFn: (id: string) => restoreTransaction(id),
  onMutate: () => (mutationError.value = ""),
  onSuccess: () => invalidateRelatedQueries(),
  onError: (error) => handleMutationError(error),
});

function handleMutationError(error: unknown) {
  mutationError.value =
    error instanceof ApiError && error.status === 409
      ? "This transaction changed elsewhere. Refreshing to resolve the conflict."
      : error instanceof Error
        ? error.message
        : "Transaction change failed.";
  if (error instanceof ApiError && error.status === 409) {
    invalidateRelatedQueries();
  }
}

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
    current: true,
  },
  {
    kind: "route" as const,
    key: "assets-liabilities",
    label: "Assets & Liabilities",
    icon: "assets",
    href: "/assets-liabilities",
  },
]);

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
) {
  const tx = transactions.value.find((t) => t.transaction_id === id);
  if (!tx) return;
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
        undoStack.value.push({
          kind: "edit",
          id,
          previous,
          expectedVersion: result.version,
        });
      },
    },
  );
}

function handleSubmit(payload: {
  date: string;
  account_id: string;
  amount_minor: number;
  category_id: string | null;
  system_category: string | null;
  status: "PENDING" | "CLEARED";
  memo: string;
}) {
  createMutation.mutate(payload);
}

function handleRemove(tx: Transaction) {
  deleteMutation.mutate(
    { id: tx.transaction_id, expectedVersion: tx.version },
    {
      onSuccess: () => {
        undoStack.value.push({ kind: "remove", snapshot: { ...tx } });
        lastRemovedSnapshot.value = { ...tx };
        showUndoToast.value = true;
        setTimeout(() => (showUndoToast.value = false), 8000);
      },
    },
  );
}

function handleUndoRemove() {
  if (!lastRemovedSnapshot.value) return;
  const tx = lastRemovedSnapshot.value;
  restoreMutation.mutate(tx.transaction_id, {
    onSuccess: () => {
      if (undoStack.value[undoStack.value.length - 1]?.kind === "remove") {
        undoStack.value.pop();
      }
      showUndoToast.value = false;
      lastRemovedSnapshot.value = null;
    },
  });
}

function handleUndo() {
  const entry = undoStack.value[undoStack.value.length - 1];
  if (!entry) return;
  if (entry.kind === "edit") {
    updateMutation.mutate(
      {
        id: entry.id,
        payload: entry.previous,
        expectedVersion: entry.expectedVersion,
      },
      { onSuccess: () => undoStack.value.pop() },
    );
  } else if (entry.kind === "remove") {
    const tx = entry.snapshot;
    restoreMutation.mutate(tx.transaction_id, {
      onSuccess: () => undoStack.value.pop(),
    });
  }
  showUndoToast.value = false;
  lastRemovedSnapshot.value = null;
}

function handleGlobalKeydown(event: KeyboardEvent) {
  const isMod = event.metaKey || event.ctrlKey;
  if (isMod && event.key === "z" && !event.shiftKey) {
    event.preventDefault();
    handleUndo();
  }
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

onMounted(() => {
  document.addEventListener("keydown", handleGlobalKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalKeydown);
});
</script>

<template>
  <div class="transactions-page" data-cy="transactions-page-root">
    <NavigationRail
      :items="navItems"
      :full-height="true"
      brand="dojo"
      aria-label="Main navigation"
    />

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

      <PersistentWarningBanner
        v-if="mutationError"
        severity="error"
        title="Transaction change failed"
        :description="mutationError"
        dismissible
        @dismiss="mutationError = ''"
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

      <Transition name="toast">
        <div v-if="showUndoToast" class="transactions-page__toast">
          <span>Transaction removed</span>
          <Button variant="tertiary" size="sm" @click="handleUndoRemove">
            Undo
          </Button>
          <Button variant="tertiary" size="sm" @click="showUndoToast = false">
            ✕
          </Button>
        </div>
      </Transition>
    </main>
  </div>
</template>

<style scoped>
.transactions-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.transactions-page__main {
  flex: 1;
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

.transactions-page__toast {
  position: fixed;
  bottom: var(--space-lg);
  right: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-on-surface);
  color: var(--color-surface);
  border-radius: var(--radius-md);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  z-index: 1001;
  box-shadow: var(--shadow-modal);
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--transition-normal) var(--transition-ease-out);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(var(--space-md));
}

@media (max-width: 720px) {
  .transactions-page__main {
    padding: var(--space-md);
  }
}
</style>
