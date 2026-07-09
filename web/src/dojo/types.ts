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

export type Allocation = {
  allocation_id: string;
  date: string;
  from_bucket_id: string;
  to_bucket_id: string;
  from_bucket_name: string;
  to_bucket_name: string;
  from_category_id: string | null;
  to_category_id: string | null;
  amount_minor: number;
  memo: string | null;
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
  goal_type: string | null;
  goal_amount_minor: number | null;
  goal_frequency: string | null;
  goal_due_date: string | null;
  available_minor: number;
  month_activity_minor: number;
  month_budgeted_minor: number;
  starting_available_minor: number;
  monthly_funding_minor: number;
  linked_account_id?: string | null;
  icon?: string | null;
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
  unconfigured_goal_count: number;
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
  validation_report?: {
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
  import_summary?: Record<string, unknown>;
  decisions_summary?: {
    duplicates_excluded: number;
    tracking_created: number;
    skipped: number;
    low_confidence_accepted: number;
  };
};

export type ReviewConfidence = "HIGH" | "MEDIUM" | "LOW" | "NONE";

export type NetWorthTreatment =
  | "DUPLICATE_BUDGET_ACCOUNT"
  | "IMPORT_TRACKING_ACCOUNT"
  | "DO_NOT_IMPORT";

export type TrackingPolarity = "ASSET" | "LIABILITY";

export type ImportReviewItem = {
  raw_name: string;
  latest_value_minor: number;
  latest_date: string;
  suggested_treatment: NetWorthTreatment;
  suggested_matched_account_id: string | null;
  suggested_matched_account_name: string | null;
  suggested_polarity: TrackingPolarity;
  suggested_polarity_reason: string;
  confidence: ReviewConfidence;
  score: number;
  reason: string;
  candidate_account_ids: string[];
  candidate_account_names: string[];
};

export type ImportReviewDecision = {
  raw_name: string;
  treatment: NetWorthTreatment;
  matched_account_id: string | null;
  polarity: TrackingPolarity | null;
};

export type ImportPreview = {
  draft_id: string;
  budget_account_count: number;
  net_worth_category_count: number;
  review_items: ImportReviewItem[];
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

export type AssetsLiabilitiesItem = Account & {
  value_minor: number;
  source_of_truth: string;
  metadata?: string;
  institution?: string | null;
  account_number_last4?: string | null;
  latest_valuation_date?: string | null;
};

export type AssetsLiabilitiesGroup = {
  key: string;
  items: AssetsLiabilitiesItem[];
  total_minor: number;
};

export type AssetsLiabilitiesResponse = {
  assets_minor: number;
  liabilities_minor: number;
  net_worth_minor: number;
  needs_attention_count: number;
  groups: AssetsLiabilitiesGroup[];
};
