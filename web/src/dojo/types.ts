export type AppStatus = {
  app: string;
  ready: boolean;
  mode: string;
  needs_onboarding: boolean;
  latest_import_batch: Record<string, unknown> | null;
  latest_import_run: Record<string, unknown> | null;
};

export type Transaction = {
  transaction_id: string;
  date: string;
  account_id: string;
  account_name: string;
  amount_minor: number;
  category_id: string | null;
  category_name: string | null;
  system_category: string | null;
  status: "PENDING" | "CLEARED";
  memo: string;
  is_hidden_entity: boolean;
};

export type Account = {
  account_id: string;
  name: string;
  account_class: string;
  is_hidden: boolean;
  is_active: boolean;
  budget_account_type?: string | null;
  linked_payment_category_id?: string | null;
  actual_balance_minor: number;
  pending_balance_minor: number;
  cleared_balance_minor: number;
  display_balance_minor: number;
};

export type Category = {
  category_id: string;
  bucket_id: string;
  group_id: string;
  group_name: string;
  name: string;
  category_kind: string;
  sort_order: number;
  is_hidden: boolean;
  is_active: boolean;
  target_amount_minor: number | null;
  due_date_rule: string | null;
  available_minor: number;
  month_activity_minor: number;
  month_budgeted_minor: number;
  starting_available_minor: number;
  linked_account_id?: string | null;
};

export type CategoryGroup = {
  group_id: string;
  name: string;
  sort_order: number;
  is_hidden: boolean;
  is_system: boolean;
  is_deletable: boolean;
  totals: {
    available_minor: number;
    month_activity_minor: number;
    month_budgeted_minor: number;
    starting_available_minor: number;
  };
  categories: Category[];
};

export type BudgetResponse = {
  month: string;
  available_to_budget_minor: number;
  summary: {
    month_activity_minor: number;
    month_budgeted_minor: number;
    starting_available_minor: number;
    reportable_income_minor: number;
    spent_minor: number;
  };
  groups: CategoryGroup[];
};

export type BootstrapResponse = {
  app_status: AppStatus;
  import_status: Record<string, unknown> | null;
  default_budget_month: string;
};

export type NetWorthItem = {
  account_name: string;
  net_worth_minor: number;
  source: string;
  ignored_import_value: boolean;
  ignored_reason?: string | null;
  match_candidates?: string[];
};

export type NetWorthResponse = {
  current_net_worth_minor: number;
  items: NetWorthItem[];
};

export type ImportResult = {
  ok: boolean;
  validation_report: {
    passed: boolean;
    checks: Array<{
      label: string;
      entity_type: string;
      entity_name: string;
      month: string | null;
      expected_value: unknown;
      actual_value: unknown;
      expected_minor: number | null;
      actual_minor: number | null;
      absolute_delta_minor: number | null;
      passed: boolean;
      source_reference: string[];
      notes: string;
    }>;
    hard_failures: Array<{
      label: string;
      entity_type: string;
      entity_name: string;
      month: string | null;
      expected_value: unknown;
      actual_value: unknown;
      expected_minor: number | null;
      actual_minor: number | null;
      absolute_delta_minor: number | null;
      passed: boolean;
      source_reference: string[];
      notes: string;
    }>;
    warnings: Array<{ code: string; message: string }>;
    summary: Record<string, unknown>;
  };
  import_batch?: Record<string, unknown>;
  app_status?: AppStatus;
  import_status?: Record<string, unknown> | null;
};

export type GoogleOnboardingStatus = {
  configured: boolean;
  fixture_mode: boolean;
  authorized: boolean;
  message: string;
  auth_url?: string | null;
};

export type TransactionPayload = {
  date: string;
  account_id: string;
  amount_minor: number;
  category_id: string | null;
  system_category: string | null;
  status: "PENDING" | "CLEARED";
  memo: string;
};
