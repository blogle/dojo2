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

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export async function fetchAppStatus(): Promise<AppStatus> {
  return request<AppStatus>("/api/app/status");
}

export async function fetchBootstrap(): Promise<BootstrapResponse> {
  return request<BootstrapResponse>("/api/bootstrap");
}

export async function fetchBudget(
  month: string,
  showHidden: boolean,
): Promise<BudgetResponse> {
  const params = new URLSearchParams({
    month,
    show_hidden: String(showHidden),
  });
  return request<BudgetResponse>(`/api/budget?${params.toString()}`);
}

export type TransactionPage = {
  items: Transaction[];
  total: number;
  offset: number;
  limit: number;
  has_more: boolean;
};

export async function fetchTransactionsPage(
  showHidden: boolean,
  offset: number,
  limit: number,
): Promise<TransactionPage> {
  const params = new URLSearchParams({
    show_hidden: String(showHidden),
    offset: String(offset),
    limit: String(limit),
    sort_by: "date",
    sort_dir: "desc",
  });
  return request<TransactionPage>(`/api/transactions?${params.toString()}`);
}

export async function fetchAccounts(showHidden: boolean): Promise<Account[]> {
  const params = new URLSearchParams({ show_hidden: String(showHidden) });
  const response = await request<{ items: Account[] }>(
    `/api/accounts?${params.toString()}`,
  );
  return response.items;
}

export async function fetchCategories(
  month: string,
  showHidden: boolean,
): Promise<{
  groups: CategoryGroup[];
  items: Category[];
}> {
  const params = new URLSearchParams({
    month,
    show_hidden: String(showHidden),
  });
  return request(`/api/categories?${params.toString()}`);
}

export async function fetchNetWorth(): Promise<NetWorthResponse> {
  return request<NetWorthResponse>("/api/net-worth");
}

export async function startGoogleOnboarding(): Promise<GoogleOnboardingStatus> {
  return request<GoogleOnboardingStatus>("/api/onboarding/google/start", {
    method: "POST",
  });
}

export async function fetchGoogleOnboardingStatus(): Promise<GoogleOnboardingStatus> {
  return request<GoogleOnboardingStatus>("/api/onboarding/google/status");
}

export async function importGoogleSheet(
  sheetUrlOrId: string,
): Promise<ImportResult> {
  return request<ImportResult>("/api/import/google-sheet", {
    method: "POST",
    body: JSON.stringify({ sheet_url_or_id: sheetUrlOrId }),
  });
}

export async function createAllocation(
  payload: {
    date: string;
    amount_minor: number;
    memo: string;
    from_bucket_id: string;
    to_bucket_id: string;
  },
  path:
    | "/api/allocations/fund"
    | "/api/allocations/move"
    | "/api/allocations/return-to-atb",
): Promise<void> {
  await request(path, { method: "POST", body: JSON.stringify(payload) });
}

export async function createTransaction(
  payload: TransactionPayload,
): Promise<void> {
  await request("/api/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTransaction(
  transactionId: string,
  payload: TransactionPayload,
): Promise<void> {
  await request(`/api/transactions/${transactionId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteTransaction(transactionId: string): Promise<void> {
  await request(`/api/transactions/${transactionId}`, { method: "DELETE" });
}

export async function createTransfer(payload: {
  date: string;
  from_account_id: string;
  to_account_id: string;
  amount_minor: number;
  status: "PENDING" | "CLEARED";
  memo: string;
}): Promise<void> {
  await request("/api/transfers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createAccount(
  payload: Record<string, unknown>,
): Promise<void> {
  await request("/api/accounts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateAccount(
  accountId: string,
  payload: Record<string, unknown>,
): Promise<void> {
  await request(`/api/accounts/${accountId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createCategoryGroup(
  payload: Record<string, unknown>,
): Promise<void> {
  await request("/api/category-groups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCategoryGroup(
  groupId: string,
  payload: Record<string, unknown>,
): Promise<void> {
  await request(`/api/category-groups/${groupId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createCategory(
  payload: Record<string, unknown>,
): Promise<void> {
  await request("/api/categories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCategory(
  categoryId: string,
  payload: Record<string, unknown>,
): Promise<void> {
  await request(`/api/categories/${categoryId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
