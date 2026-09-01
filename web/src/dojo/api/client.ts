import type {
  Account,
  Allocation,
  AppStatus,
  AssetsLiabilitiesResponse,
  BootstrapResponse,
  BudgetResponse,
  CategoryActivity,
  Category,
  CategoryGroup,
  GoogleOnboardingStatus,
  ImportPreview,
  ImportResult,
  NetWorthResponse,
  Transaction,
  TransactionPayload,
} from "../types";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

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
  status_counts: {
    PENDING: number;
    CLEARED: number;
  };
};

export type TransactionFilters = {
  accountId?: string;
  categoryId?: string;
  status?: "PENDING" | "CLEARED";
  dateFrom?: string;
  dateTo?: string;
  amountMinMinor?: number;
  amountMaxMinor?: number;
  sortBy?: "date" | "amount_minor" | "status" | "created_at" | "entry_order";
  sortDir?: "asc" | "desc";
};

export async function fetchTransactionsPage(
  showHidden: boolean,
  offset: number,
  limit: number,
  filters: TransactionFilters = {},
): Promise<TransactionPage> {
  const params = new URLSearchParams({
    show_hidden: String(showHidden),
    offset: String(offset),
    limit: String(limit),
    sort_by: filters.sortBy ?? "created_at",
    sort_dir: filters.sortDir ?? "desc",
  });
  if (filters.accountId) params.set("account_id", filters.accountId);
  if (filters.categoryId) params.set("category_id", filters.categoryId);
  if (filters.status) params.set("status", filters.status);
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  if (filters.amountMinMinor !== undefined) {
    params.set("amount_min_minor", String(filters.amountMinMinor));
  }
  if (filters.amountMaxMinor !== undefined) {
    params.set("amount_max_minor", String(filters.amountMaxMinor));
  }
  return request<TransactionPage>(`/api/transactions?${params.toString()}`);
}

export async function fetchAccounts(showHidden: boolean): Promise<Account[]> {
  const params = new URLSearchParams({ show_hidden: String(showHidden) });
  const response = await request<{ items: Account[] }>(
    `/api/accounts?${params.toString()}`,
  );
  return response.items;
}

export type AccountTransactionSummary = {
  inflow_minor: number;
  outflow_minor: number;
  net_flow_minor: number;
  transaction_count: number;
  average_daily_balance_minor: number;
};

export async function fetchAccountTransactionSummary(
  accountId: string,
  days = 30,
): Promise<AccountTransactionSummary> {
  const params = new URLSearchParams({ days: String(days) });
  return request<AccountTransactionSummary>(
    `/api/accounts/${accountId}/transactions/summary?${params.toString()}`,
  );
}

export type BalanceTrendPointApi = {
  date: string;
  balance_minor: number;
};

export async function fetchAccountBalanceTrend(
  accountId: string,
  period: string,
): Promise<{ points: BalanceTrendPointApi[] }> {
  const params = new URLSearchParams({ period });
  return request<{ points: BalanceTrendPointApi[] }>(
    `/api/accounts/${accountId}/balance-trend?${params.toString()}`,
  );
}

export async function fetchAllocations(
  showHidden: boolean,
): Promise<Allocation[]> {
  const params = new URLSearchParams({ show_hidden: String(showHidden) });
  const response = await request<{ items: Allocation[] }>(
    `/api/allocations?${params.toString()}`,
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

export async function fetchCategoryActivity(): Promise<CategoryActivity[]> {
  const response = await request<{ items: CategoryActivity[] }>(
    "/api/category-activity",
  );
  return response.items;
}

export async function fetchNetWorth(): Promise<NetWorthResponse> {
  return request<NetWorthResponse>("/api/net-worth");
}

export async function fetchAssetsLiabilities(): Promise<AssetsLiabilitiesResponse> {
  return request<AssetsLiabilitiesResponse>("/api/assets-liabilities");
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

export async function analyzeGoogleSheet(
  sheetUrlOrId: string,
): Promise<ImportPreview> {
  return request<ImportPreview>("/api/import/google-sheet/analyze", {
    method: "POST",
    body: JSON.stringify({ sheet_url_or_id: sheetUrlOrId }),
  });
}

export async function commitGoogleSheetImport(payload: {
  draft_id: string;
  decisions: Array<{
    raw_name: string;
    treatment: string;
    matched_account_id: string | null;
    polarity: string | null;
  }>;
  low_confidence_confirmed: boolean;
}): Promise<ImportResult> {
  return request<ImportResult>("/api/import/google-sheet/commit", {
    method: "POST",
    body: JSON.stringify(payload),
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
  path: "/api/allocations/move" | "/api/allocations/return-to-atb",
): Promise<void> {
  await request(path, { method: "POST", body: JSON.stringify(payload) });
}

export async function fundCategory(payload: {
  client_operation_id: string;
  date: string;
  category_id: string;
  amount_minor: number;
  memo: string;
}): Promise<{ allocation_id: string }> {
  return request("/api/allocations/fund", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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

export async function restoreTransaction(transactionId: string): Promise<void> {
  await request(`/api/transactions/${transactionId}/restore`, {
    method: "POST",
  });
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
): Promise<{ account_id: string }> {
  return request("/api/accounts", {
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

export type TrackingSnapshot = {
  valuation_id: string;
  account_id: string;
  effective_date: string;
  amount_minor: number;
  notes: string;
  metadata?: string | null;
};

export async function fetchTrackingSnapshots(
  accountId: string,
): Promise<TrackingSnapshot[]> {
  const response = await request<{ items: TrackingSnapshot[] }>(
    `/api/accounts/${accountId}/tracking-snapshots`,
  );
  return response.items;
}

export async function createTrackingSnapshot(
  accountId: string,
  payload: {
    effective_date: string;
    amount_minor: number;
    source?: string;
    notes?: string;
  },
): Promise<{ valuation_id: string }> {
  return request<{ valuation_id: string }>(
    `/api/accounts/${accountId}/tracking-snapshots`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export type TrackingCutoverSuccessor =
  | {
      account_class: "INVESTMENT";
      name: string;
      institution?: string;
      contribution_category_id?: string;
      cash_balance_minor: number;
      holdings: Array<{
        ticker: string;
        quantity_micros: number;
        price_minor: number;
        average_basis_minor: number;
      }>;
    }
  | {
      account_class: "LOAN";
      name: string;
      institution?: string;
      payment_category_id: string;
      principal_balance_minor: number;
      accrued_interest_minor?: number;
      escrow_balance_minor: number;
      unapplied_credit_minor?: number;
    }
  | {
      account_class: "TANGIBLE_ASSET";
      name: string;
      institution?: string;
      opening_value_minor: number;
    };

export async function createTrackingCutover(
  accountId: string,
  payload: {
    operation_id: string;
    cutover_date: string;
    expected_predecessor_value_minor: number;
    final_predecessor_value_minor: number;
    successors: TrackingCutoverSuccessor[];
  },
): Promise<{
  operation_id: string;
  predecessor_account_id: string;
  cutover_date: string;
  prior_value_minor: number;
  successor_total_minor: number;
  variance_minor: number;
  successor_account_ids: string[];
}> {
  return request(`/api/accounts/${accountId}/cutovers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type TangibleValuation = {
  valuation_id: string;
  account_id: string;
  effective_date: string;
  amount_minor: number;
  source: string;
  notes: string;
};

export async function fetchTangibleValuations(
  accountId: string,
): Promise<TangibleValuation[]> {
  const response = await request<{ items: TangibleValuation[] }>(
    `/api/accounts/${accountId}/tangible-valuations`,
  );
  return response.items;
}

export async function createTangibleValuation(
  accountId: string,
  payload: {
    effective_date: string;
    amount_minor: number;
    source?: string;
    notes?: string;
  },
): Promise<{ valuation_id: string }> {
  return request<{ valuation_id: string }>(
    `/api/accounts/${accountId}/tangible-valuations`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export type InvestmentStatementHolding = {
  position_id: string;
  ticker: string;
  quantity_micros: number;
  average_basis_minor: number;
  price_minor: number;
  value_minor: number;
  cost_basis_minor: number;
  unrealized_gain_minor: number;
};

export type InvestmentStatement = {
  effective_date: string | null;
  cash_balance_minor: number | null;
  holdings: InvestmentStatementHolding[];
  holdings_value_minor: number | null;
  holdings_cost_basis_minor: number | null;
  unrealized_gain_minor: number | null;
  current_value_minor: number | null;
  provisional_transfer_minor: number;
};

export async function fetchLatestInvestmentStatement(
  accountId: string,
): Promise<InvestmentStatement> {
  return request<InvestmentStatement>(
    `/api/accounts/${accountId}/investment-statements/latest`,
  );
}

export async function reconcileInvestmentStatement(
  accountId: string,
  payload: {
    effective_date: string;
    cash_balance_minor: number;
    holdings: Array<{
      ticker: string;
      quantity_micros: number;
      price_minor: number;
      average_basis_minor: number;
    }>;
    notes?: string;
  },
): Promise<{ effective_date: string }> {
  return request(`/api/accounts/${accountId}/investment-statements`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type ReconciliationSourceRecord = {
  source_record_id: string;
  posted_date: string;
  cleared_date?: string | null;
  signed_amount_minor: number;
  source_status: "PENDING" | "CLEARED";
  description?: string;
  transaction_id?: string | null;
  raw_payload?: Record<string, unknown> | null;
};

export type ReconciliationDraft = {
  reconciliation_id: string;
  account_id: string;
  state: string;
  source_kind: string;
  cutoff: string;
  source_ending_value_minor: number;
  ledger_value_minor: number;
  difference_minor: number;
  baseline_digest: string;
  classifications: Record<string, unknown>;
};

export async function createReconciliationDraft(
  accountId: string,
  payload: {
    source_kind:
      | "BANK_STATEMENT"
      | "CREDIT_CARD_STATEMENT"
      | "INVESTMENT_STATEMENT";
    period_start?: string;
    cutoff: string;
    source_ending_value_minor: number;
    source_records?: ReconciliationSourceRecord[];
  },
): Promise<ReconciliationDraft> {
  return request(`/api/accounts/${accountId}/reconciliations/draft`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function applyReconciliation(
  reconciliationId: string,
  payload: {
    client_operation_id: string;
    balance_adjustment_minor?: number | null;
  },
): Promise<Record<string, unknown>> {
  return request(`/api/reconciliations/${reconciliationId}/apply`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchReconciliationWorkingSet(
  accountId: string,
): Promise<Record<string, unknown>> {
  return request(`/api/accounts/${accountId}/reconciliation-working-set`);
}

export type AccountBudgetLink = {
  account_id: string;
  category_id: string;
  link_behavior: string;
  derivation_method: string;
  effective_date: string;
};

export async function fetchAccountBudgetLinks(
  accountId: string,
): Promise<AccountBudgetLink[]> {
  const response = await request<{ items: AccountBudgetLink[] }>(
    `/api/accounts/${accountId}/budget-links`,
  );
  return response.items;
}

export async function setAccountBudgetLink(
  accountId: string,
  payload: {
    category_id: string;
    link_behavior: "INVESTMENT_CONTRIBUTION" | "LOAN_PAYMENT";
    effective_date: string;
  },
): Promise<void> {
  await request(`/api/accounts/${accountId}/budget-links`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function createInvestmentTransfer(
  accountId: string,
  payload: {
    direction: "CONTRIBUTION" | "WITHDRAWAL";
    client_operation_id: string;
    source_account_id: string;
    source_posted_date: string;
    source_status: "PENDING" | "CLEARED";
    destination_account_id: string;
    destination_posted_date: string;
    destination_status: "PENDING" | "CLEARED";
    amount_minor: number;
    memo: string;
  },
): Promise<{
  source_transaction_id: string;
  destination_transaction_id: string;
  linked_category_id: string | null;
}> {
  return request(`/api/accounts/${accountId}/investment-transfers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createCreditCardPayment(
  accountId: string,
  payload: {
    client_operation_id: string;
    source_account_id: string;
    source_posted_date: string;
    source_status: "PENDING" | "CLEARED";
    destination_account_id: string;
    destination_posted_date: string;
    destination_status: "PENDING" | "CLEARED";
    amount_minor: number;
    memo: string;
  },
): Promise<Record<string, unknown>> {
  return request(`/api/accounts/${accountId}/credit-card-payments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type LoanSnapshot = {
  snapshot_id: string;
  account_id: string;
  effective_date: string;
  principal_balance_minor: number;
  accrued_interest_minor: number | null;
  escrow_balance_minor: number;
  unapplied_credit_minor: number | null;
  ytd_principal_paid_minor: number | null;
  ytd_interest_paid_minor: number | null;
  attributed_payment_minor: number;
  principal_reduction_minor: number;
  unknown_nonprincipal_minor: number;
  notes: string;
};

export type LoanProjection = {
  available: boolean;
  missing: string[];
  reason?: string;
  rate_assumption?: string;
  estimated_accrued_interest_minor?: number;
  projected_payoff_date?: string | null;
  projected_total_interest_minor?: number;
  remaining_principal_at_horizon_minor?: number;
  rows: Array<{
    payment_number: number;
    payment_date: string;
    payment_minor: number;
    principal_minor: number;
    interest_minor: number;
    remaining_principal_minor: number;
  }>;
};

export async function fetchLoanSnapshots(
  accountId: string,
): Promise<LoanSnapshot[]> {
  const response = await request<{ items: LoanSnapshot[] }>(
    `/api/accounts/${accountId}/loan-snapshots`,
  );
  return response.items;
}

export async function fetchLoanProjection(
  accountId: string,
): Promise<LoanProjection> {
  return request<LoanProjection>(`/api/accounts/${accountId}/loan-projection`);
}

export async function reconcileLoanStatement(
  accountId: string,
  payload: {
    effective_date: string;
    principal_balance_minor: number;
    accrued_interest_minor?: number;
    escrow_balance_minor: number;
    unapplied_credit_minor?: number;
    ytd_principal_paid_minor?: number;
    ytd_interest_paid_minor?: number;
    notes?: string;
  },
): Promise<{ snapshot_id: string }> {
  return request(`/api/accounts/${accountId}/loan-snapshots`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createLoanPayment(
  accountId: string,
  payload: {
    date: string;
    budget_account_id: string;
    amount_minor: number;
    status: "PENDING" | "CLEARED";
    memo: string;
  },
): Promise<{ transaction_id: string }> {
  return request(`/api/accounts/${accountId}/loan-payments`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchLoanPayments(
  accountId: string,
): Promise<Transaction[]> {
  const response = await request<{ items: Transaction[] }>(
    `/api/accounts/${accountId}/loan-payments`,
  );
  return response.items;
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

export async function fetchCategoryGoal(categoryId: string): Promise<{
  category_id: string;
  goal_type: string | null;
  goal_amount_minor: number | null;
  goal_frequency: string | null;
  goal_due_date: string | null;
  monthly_funding_minor: number;
}> {
  return request(`/api/categories/${categoryId}/goal`);
}

export async function updateCategoryGoal(
  categoryId: string,
  payload: {
    goal_type?: string | null;
    goal_amount_minor?: number | null;
    goal_frequency?: string | null;
    goal_due_date?: string | null;
  },
): Promise<void> {
  await request(`/api/categories/${categoryId}/goal`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
