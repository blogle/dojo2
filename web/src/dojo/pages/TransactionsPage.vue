<script setup lang="ts">
import { computed, ref, onMounted } from "vue";

import type { Transaction } from "../types";
import { useAppState } from "../state/app";
import { formatCurrency, formatMonth } from "../utils/currency";

import NavigationRail from "../components/navigation/NavigationRail.vue";
import PageHeader from "../components/data/PageHeader.vue";
import MetricStrip from "../components/data/MetricStrip.vue";
import type { MetricStripItem } from "../components/data/MetricStrip.vue";
import Button from "../components/actions/Button.vue";
import TransactionEntryForm from "../components/transactions/TransactionEntryForm.vue";
import TransactionFilterBar from "../components/transactions/TransactionFilterBar.vue";
import TransactionLedger from "../components/transactions/TransactionLedger.vue";

const {
  state,
  initialize,
  submitTransaction,
  removeTransaction,
  toggleTransactionStatus,
} = useAppState();

const selectedMonth = ref("");
const editingTransaction = ref<Transaction | null>(null);
const removingTransaction = ref<Transaction | null>(null);
const showUndoToast = ref(false);
const lastRemovedId = ref<string | null>(null);

const currentMonth = computed(() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
});

const monthTransactions = computed(() => {
  if (!selectedMonth.value) return [];
  return state.transactions.filter((t) => {
    const txMonth = t.date.slice(0, 7);
    return txMonth === selectedMonth.value;
  });
});

const inflow = computed(() =>
  monthTransactions.value
    .filter((t) => t.amount_minor > 0)
    .reduce((sum, t) => sum + t.amount_minor, 0),
);

const outflow = computed(() =>
  monthTransactions.value
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

function previousMonth() {
  const [year, month] = selectedMonth.value.split("-").map(Number);
  const prev = month === 1 ? 12 : month - 1;
  const yr = month === 1 ? year - 1 : year;
  selectedMonth.value = `${yr}-${String(prev).padStart(2, "0")}`;
}

function nextMonth() {
  const [year, month] = selectedMonth.value.split("-").map(Number);
  const nxt = month === 12 ? 1 : month + 1;
  const yr = month === 12 ? year + 1 : year;
  selectedMonth.value = `${yr}-${String(nxt).padStart(2, "0")}`;
}

function handleEditTransaction(tx: Transaction) {
  editingTransaction.value = tx;
}

function handleCancelEdit() {
  editingTransaction.value = null;
}

async function handleSaveEdit(payload: {
  date: string;
  account_id: string;
  amount_minor: number;
  category_id: string | null;
  system_category: string | null;
  status: "PENDING" | "CLEARED";
  memo: string;
}) {
  if (!editingTransaction.value) return;
  await submitTransaction(payload);
  editingTransaction.value = null;
}

function handleRemoveRequest(tx: Transaction) {
  removingTransaction.value = tx;
}

async function confirmRemove() {
  if (!removingTransaction.value) return;
  const id = removingTransaction.value.transaction_id;
  lastRemovedId.value = id;
  await removeTransaction(id);
  removingTransaction.value = null;
  showUndoToast.value = true;
  setTimeout(() => {
    showUndoToast.value = false;
  }, 8000);
}

function cancelRemove() {
  removingTransaction.value = null;
}

async function handleUndoRemove() {
  if (!lastRemovedId.value) return;
  // Re-enable the removed transaction by updating it
  const tx = state.transactions.find(
    (t) => t.transaction_id === lastRemovedId.value,
  );
  if (tx) {
    await submitTransaction({
      date: tx.date,
      account_id: tx.account_id,
      amount_minor: tx.amount_minor,
      category_id: tx.category_id,
      system_category: tx.system_category,
      status: tx.status,
      memo: tx.memo,
    });
  }
  showUndoToast.value = false;
  lastRemovedId.value = null;
}

onMounted(() => {
  initialize().then(() => {
    selectedMonth.value = state.month || currentMonth.value;
  });
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
          {{ formatMonth(selectedMonth || currentMonth) }}
        </span>
        <Button variant="tertiary" size="sm" @click="previousMonth">
          &lt;
        </Button>
        <Button variant="tertiary" size="sm" @click="nextMonth">
          &gt;
        </Button>
      </div>

      <MetricStrip :items="metrics" />

      <TransactionEntryForm
        :accounts="state.accounts"
        :categories="state.categories"
        :editing-transaction="editingTransaction"
        @submit="submitTransaction"
        @cancel-edit="handleCancelEdit"
        @save-edit="handleSaveEdit"
      />

      <TransactionFilterBar
        :accounts="state.accounts"
        :categories="state.categories"
      />

      <TransactionLedger
        :transactions="monthTransactions"
        :accounts="state.accounts"
        :categories="state.categories"
        :editing-transaction-id="editingTransaction?.transaction_id ?? null"
        @edit="handleEditTransaction"
        @remove="handleRemoveRequest"
        @toggle-status="toggleTransactionStatus"
      />

      <div v-if="removingTransaction" class="transactions-page__modal-scrim">
        <div
          class="transactions-page__confirm-modal"
          role="dialog"
          aria-modal="true"
        >
          <div class="transactions-page__confirm-icon">⚠</div>
          <h2 class="transactions-page__confirm-title">Remove transaction?</h2>
          <p class="transactions-page__confirm-text">
            This transaction will be removed and marked as inactive. It will no
            longer be included in your totals or reports.
          </p>
          <div class="transactions-page__confirm-actions">
            <Button variant="secondary" @click="cancelRemove">Cancel</Button>
            <Button variant="primary" @click="confirmRemove">Remove</Button>
          </div>
        </div>
      </div>

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

.transactions-page__modal-scrim {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.transactions-page__confirm-modal {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  max-width: 420px;
  width: 90%;
  text-align: center;
  box-shadow: var(--shadow-modal);
}

.transactions-page__confirm-icon {
  font-size: 32px;
  margin-bottom: var(--space-md);
  color: var(--color-warning);
}

.transactions-page__confirm-title {
  margin: 0 0 var(--space-sm);
  font-family: var(--text-heading-md-font-family);
  font-size: var(--text-heading-md-font-size);
  font-weight: var(--text-heading-md-font-weight);
  color: var(--color-on-surface);
}

.transactions-page__confirm-text {
  margin: 0 0 var(--space-lg);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  color: var(--color-on-surface-muted);
  line-height: var(--text-body-md-line-height);
}

.transactions-page__confirm-actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: center;
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
