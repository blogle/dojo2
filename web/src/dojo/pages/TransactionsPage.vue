<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useQuery, useMutation, useQueryClient } from "@tanstack/vue-query";

import type { Transaction, TransactionPayload } from "../types";
import { formatCurrency, formatMonth } from "../utils/currency";
import {
  fetchTransactionsPage,
  fetchAccounts,
  fetchCategories,
  createTransaction,
  updateTransaction,
  deleteTransaction,
  restoreTransaction,
} from "../api/client";

import NavigationRail from "../components/navigation/NavigationRail.vue";
import PageHeader from "../components/data/PageHeader.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import type { MetricStripItem } from "../components/data/MetricStrip.vue";
import Button from "../components/actions/Button.vue";
import TransactionEntryForm from "../components/transactions/TransactionEntryForm.vue";
import TransactionFilterBar from "../components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "../components/transactions/TransactionLedger.vue";

const queryClient = useQueryClient();

const PAGE_SIZE = 10_000;
const QUERY_KEYS = {
  transactions: ["transactions", PAGE_SIZE] as const,
  accounts: ["accounts"] as const,
  categories: ["categories"] as const,
  budget: ["budget"] as const,
  allocations: ["allocations"] as const,
  netWorth: ["net-worth"] as const,
} as const;

type UndoEntry =
  | { kind: "edit"; id: string; previous: TransactionPayload }
  | { kind: "remove"; snapshot: Transaction };

const undoStack = ref<UndoEntry[]>([]);
const showUndoToast = ref(false);
const lastRemovedSnapshot = ref<Transaction | null>(null);

const currentMonth = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
});

const { data: txPage } = useQuery({
  queryKey: QUERY_KEYS.transactions,
  queryFn: () => fetchTransactionsPage(false, 0, PAGE_SIZE),
});

const transactions = computed(() => txPage.value?.items ?? []);

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
}

const createMutation = useMutation({
  mutationFn: createTransaction,
  onSuccess: () => invalidateRelatedQueries(),
});

const updateMutation = useMutation({
  mutationFn: ({
    id,
    payload,
  }: {
    id: string;
    payload: Parameters<typeof updateTransaction>[1];
  }) => updateTransaction(id, payload),
  onSuccess: () => invalidateRelatedQueries(),
});

const deleteMutation = useMutation({
  mutationFn: deleteTransaction,
  onSuccess: () => invalidateRelatedQueries(),
});

const restoreMutation = useMutation({
  mutationFn: restoreTransaction,
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

const navItems = computed(() => [
  {
    kind: "route" as const,
    key: "home",
    label: "Home",
    icon: "foundations",
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
    key: "assets",
    label: "Assets",
    icon: "assets",
    href: "/assets",
  },
]);

const metrics = computed<MetricStripItem[]>(() => [
  {
    key: "inflow",
    label: "Inflow",
    value: formatCurrency(inflow.value),
  },
  {
    key: "outflow",
    label: "Outflow",
    value: formatCurrency(outflow.value),
  },
  {
    key: "net",
    label: "Net",
    value: formatCurrency(net.value),
  },
]);

function handleCommitEdit(
  id: string,
  payload: Parameters<typeof updateTransaction>[1],
) {
  const tx = transactions.value.find((t) => t.transaction_id === id);
  if (tx) {
    undoStack.value.push({
      kind: "edit",
      id,
      previous: {
        date: tx.date,
        account_id: tx.account_id,
        amount_minor: tx.amount_minor,
        category_id: tx.category_id,
        system_category: tx.system_category,
        status: tx.status,
        memo: tx.memo,
      },
    });
  }
  updateMutation.mutate({ id, payload });
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
  undoStack.value.push({ kind: "remove", snapshot: { ...tx } });
  lastRemovedSnapshot.value = { ...tx };
  deleteMutation.mutate(tx.transaction_id);
  showUndoToast.value = true;
  setTimeout(() => {
    showUndoToast.value = false;
  }, 8000);
}

function handleUndoRemove() {
  if (!lastRemovedSnapshot.value) return;
  const tx = lastRemovedSnapshot.value;
  restoreMutation.mutate(tx.transaction_id);
  showUndoToast.value = false;
  lastRemovedSnapshot.value = null;
}

function handleUndo() {
  const entry = undoStack.value.pop();
  if (!entry) return;
  if (entry.kind === "edit") {
    updateMutation.mutate({ id: entry.id, payload: entry.previous });
  } else if (entry.kind === "remove") {
    const tx = entry.snapshot;
    restoreMutation.mutate(tx.transaction_id);
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

      <TransactionFilterBar
        :accounts="accounts ?? []"
        :categories="categories"
      />

      <TransactionLedger
        :transactions="transactions"
        :accounts="accounts ?? []"
        :categories="categories"
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
  margin-left: var(--space-nav-collapsed);
  padding: var(--space-page-block) var(--space-page-inline);
  display: grid;
  gap: var(--space-lg);
  align-content: start;
  position: relative;
}

.transactions-page__main :deep(.metric-strip__item) {
  flex: 1;
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
    margin-left: 0;
    padding: var(--space-md);
  }
}
</style>
