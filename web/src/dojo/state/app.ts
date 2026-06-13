import { computed, reactive } from "vue";

import {
  createAccount,
  createAllocation,
  createCategory,
  createCategoryGroup,
  createTransaction,
  createTransfer,
  deleteTransaction,
  fetchAccounts,
  fetchBootstrap,
  fetchBudget,
  fetchCategories,
  fetchGoogleOnboardingStatus,
  fetchNetWorth,
  fetchTransactionsPage,
  importGoogleSheet,
  startGoogleOnboarding,
  updateAccount,
  updateCategory,
  updateCategoryGroup,
  updateTransaction,
} from "../api/client";
import type {
  Account,
  AppStatus,
  BootstrapResponse,
  BudgetResponse,
  Category,
  CategoryGroup,
  GoogleOnboardingStatus,
  ImportResult,
  NetWorthResponse,
  Transaction,
  TransactionPayload,
} from "../types";

const state = reactive({
  loading: false,
  saving: false,
  error: "",
  showHidden: false,
  month: "",
  appStatus: null as AppStatus | null,
  bootstrap: null as BootstrapResponse | null,
  budget: null as BudgetResponse | null,
  transactions: [] as Transaction[],
  accounts: [] as Account[],
  categoryGroups: [] as CategoryGroup[],
  categories: [] as Category[],
  netWorth: null as NetWorthResponse | null,
  importResult: null as ImportResult | null,
  onboardingInfo: null as GoogleOnboardingStatus | null,
  editingTransactionId: null as string | null,
  transactionOffset: 0,
  transactionTotal: 0,
  hasMoreTransactions: false,
});

function resetState(): void {
  state.loading = false;
  state.saving = false;
  state.error = "";
  state.showHidden = false;
  state.month = "";
  state.appStatus = null;
  state.bootstrap = null;
  state.budget = null;
  state.transactions = [];
  state.accounts = [];
  state.categoryGroups = [];
  state.categories = [];
  state.netWorth = null;
  state.importResult = null;
  state.onboardingInfo = null;
  state.editingTransactionId = null;
  state.transactionOffset = 0;
  state.transactionTotal = 0;
  state.hasMoreTransactions = false;
}

async function withLoading<T>(fn: () => Promise<T>): Promise<T> {
  state.loading = true;
  state.error = "";
  try {
    return await fn();
  } catch (error) {
    state.error = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    state.loading = false;
  }
}

async function withSaving<T>(fn: () => Promise<T>): Promise<T> {
  state.saving = true;
  state.error = "";
  try {
    return await fn();
  } catch (error) {
    state.error = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    state.saving = false;
  }
}

async function refreshBootstrap(): Promise<void> {
  const bootstrap = await fetchBootstrap();
  state.bootstrap = bootstrap;
  state.appStatus = bootstrap.app_status;
  if (!state.month) {
    state.month = bootstrap.default_budget_month;
  }
}

async function refreshBudget(): Promise<void> {
  if (!state.month) {
    state.month = new Date().toISOString().slice(0, 7);
  }
  state.budget = await fetchBudget(state.month, state.showHidden);
  state.categoryGroups = state.budget.groups;
  state.categories = state.budget.groups.flatMap((group) => group.categories);
}

const PAGE_SIZE = 100;

async function fetchTransactionPage(offset: number): Promise<void> {
  const page = await fetchTransactionsPage(state.showHidden, offset, PAGE_SIZE);
  state.transactions = page.items;
  state.transactionOffset = page.offset;
  state.transactionTotal = page.total;
  state.hasMoreTransactions = page.has_more;
}

async function refreshTransactions(): Promise<void> {
  await fetchTransactionPage(0);
}

async function loadMoreTransactions(): Promise<void> {
  if (!state.hasMoreTransactions) return;
  await withLoading(async () => {
    await fetchTransactionPage(state.transactionOffset + PAGE_SIZE);
  });
}

async function loadPreviousTransactions(): Promise<void> {
  if (state.transactionOffset === 0) return;
  await withLoading(async () => {
    await fetchTransactionPage(
      Math.max(0, state.transactionOffset - PAGE_SIZE),
    );
  });
}

async function refreshAccounts(): Promise<void> {
  state.accounts = await fetchAccounts(state.showHidden);
}

async function refreshCategories(): Promise<void> {
  const response = await fetchCategories(state.month, state.showHidden);
  state.categoryGroups = response.groups;
  state.categories = response.items;
}

async function refreshNetWorth(): Promise<void> {
  state.netWorth = await fetchNetWorth();
}

async function initialize(): Promise<void> {
  await withLoading(async () => {
    await refreshBootstrap();
    if (state.appStatus?.ready) {
      await Promise.all([
        refreshBudget(),
        refreshTransactions(),
        refreshAccounts(),
        refreshNetWorth(),
      ]);
      return;
    }
    state.onboardingInfo = await fetchGoogleOnboardingStatus();
  });
}

async function importSheet(sheetUrlOrId: string): Promise<void> {
  await withSaving(async () => {
    state.importResult = await importGoogleSheet(sheetUrlOrId);
    await initialize();
  });
}

async function beginGoogleOnboarding(): Promise<void> {
  await withSaving(async () => {
    const onboarding = await startGoogleOnboarding();
    state.onboardingInfo = onboarding;
    if (!onboarding.configured || !onboarding.auth_url) {
      return;
    }

    const apiOrigin = new URL(
      import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
    ).origin;
    const popup = window.open(
      onboarding.auth_url,
      "dojo-google-oauth",
      "width=560,height=720",
    );
    if (!popup) {
      throw new Error(
        "Popup was blocked. Allow popups for this site and try again.",
      );
    }
    const popupWindow = popup;

    await new Promise<void>((resolve, reject) => {
      let finished = false;
      const timer = window.setInterval(() => {
        if (!popupWindow.closed || finished) {
          return;
        }
        finished = true;
        window.clearInterval(timer);
        window.removeEventListener("message", handleMessage);
        reject(
          new Error(
            "Google OAuth window was closed before access was granted.",
          ),
        );
      }, 250);

      function cleanup(): void {
        finished = true;
        window.clearInterval(timer);
        window.removeEventListener("message", handleMessage);
      }

      function handleMessage(event: MessageEvent): void {
        if (event.origin !== apiOrigin || finished) {
          return;
        }
        const payload = event.data as { type?: string; ok?: boolean };
        if (payload.type !== "dojo-google-oauth") {
          return;
        }
        cleanup();
        popupWindow.close();
        if (payload.ok) {
          resolve();
          return;
        }
        reject(new Error("Google OAuth did not complete successfully."));
      }

      window.addEventListener("message", handleMessage);
    });

    state.onboardingInfo = await fetchGoogleOnboardingStatus();
  });
}

async function setMonth(month: string): Promise<void> {
  state.month = month;
  await withLoading(async () => {
    await Promise.all([refreshBudget(), refreshCategories()]);
  });
}

async function setShowHidden(value: boolean): Promise<void> {
  state.showHidden = value;
  await withLoading(async () => {
    await Promise.all([
      refreshBudget(),
      refreshTransactions(),
      refreshAccounts(),
      refreshCategories(),
      refreshNetWorth(),
    ]);
  });
}

async function submitAllocation(payload: {
  date: string;
  amount_minor: number;
  memo: string;
  from_bucket_id: string;
  to_bucket_id: string;
  path:
    | "/api/allocations/fund"
    | "/api/allocations/move"
    | "/api/allocations/return-to-atb";
}): Promise<void> {
  await withSaving(async () => {
    await createAllocation(payload, payload.path);
    await Promise.all([refreshBudget(), refreshCategories()]);
  });
}

async function submitTransaction(payload: TransactionPayload): Promise<void> {
  await withSaving(async () => {
    if (state.editingTransactionId) {
      await updateTransaction(state.editingTransactionId, payload);
      state.editingTransactionId = null;
    } else {
      await createTransaction(payload);
    }
    await Promise.all([
      refreshTransactions(),
      refreshAccounts(),
      refreshBudget(),
      refreshNetWorth(),
    ]);
  });
}

async function removeTransaction(transactionId: string): Promise<void> {
  await withSaving(async () => {
    await deleteTransaction(transactionId);
    await Promise.all([
      refreshTransactions(),
      refreshAccounts(),
      refreshBudget(),
      refreshNetWorth(),
    ]);
  });
}

async function toggleTransactionStatus(
  transaction: Transaction,
): Promise<void> {
  await submitTransaction({
    date: transaction.date,
    account_id: transaction.account_id,
    amount_minor: transaction.amount_minor,
    category_id: transaction.category_id,
    system_category: transaction.system_category,
    status: transaction.status === "PENDING" ? "CLEARED" : "PENDING",
    memo: transaction.memo,
  });
}

async function submitTransfer(payload: {
  date: string;
  from_account_id: string;
  to_account_id: string;
  amount_minor: number;
  status: "PENDING" | "CLEARED";
  memo: string;
}): Promise<void> {
  await withSaving(async () => {
    await createTransfer(payload);
    await Promise.all([
      refreshTransactions(),
      refreshAccounts(),
      refreshBudget(),
      refreshNetWorth(),
    ]);
  });
}

async function saveAccount(
  payload: Record<string, unknown>,
  accountId?: string,
): Promise<void> {
  await withSaving(async () => {
    if (accountId) {
      await updateAccount(accountId, payload);
    } else {
      await createAccount(payload);
    }
    await Promise.all([refreshAccounts(), refreshNetWorth()]);
  });
}

async function saveCategoryGroup(
  payload: Record<string, unknown>,
  groupId?: string,
): Promise<void> {
  await withSaving(async () => {
    if (groupId) {
      await updateCategoryGroup(groupId, payload);
    } else {
      await createCategoryGroup(payload);
    }
    await refreshCategories();
  });
}

async function saveCategory(
  payload: Record<string, unknown>,
  categoryId?: string,
): Promise<void> {
  await withSaving(async () => {
    if (categoryId) {
      await updateCategory(categoryId, payload);
    } else {
      await createCategory(payload);
    }
    await Promise.all([refreshCategories(), refreshBudget()]);
  });
}

const ready = computed(() => Boolean(state.appStatus?.ready));

export function useAppState() {
  return {
    state,
    ready,
    resetState,
    initialize,
    importSheet,
    beginGoogleOnboarding,
    setMonth,
    setShowHidden,
    submitAllocation,
    submitTransaction,
    removeTransaction,
    toggleTransactionStatus,
    submitTransfer,
    saveAccount,
    saveCategoryGroup,
    saveCategory,
    loadMoreTransactions,
    loadPreviousTransactions,
    refreshBudget,
    refreshTransactions,
    refreshAccounts,
    refreshCategories,
    refreshNetWorth,
  };
}
