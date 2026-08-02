CREATE TABLE IF NOT EXISTS import_runs (
    import_run_id UUID PRIMARY KEY,
    spreadsheet_id TEXT NOT NULL,
    spreadsheet_title TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    validation_passed BOOLEAN NOT NULL DEFAULT FALSE,
    summary JSON,
    validation_report JSON,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS import_batches (
    import_batch_id UUID PRIMARY KEY,
    spreadsheet_id TEXT NOT NULL,
    spreadsheet_title TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL,
    cutover_at TIMESTAMPTZ NOT NULL,
    summary JSON
);

CREATE TABLE IF NOT EXISTS import_drafts (
    draft_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    source_kind TEXT NOT NULL,
    spreadsheet_id TEXT NOT NULL,
    spreadsheet_title TEXT,
    payload JSON NOT NULL,
    preview JSON NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS accounts (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    account_class TEXT NOT NULL,
    name TEXT NOT NULL,
    institution TEXT,
    account_number_last4 TEXT,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSON,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS budget_account_settings (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    budget_account_type TEXT NOT NULL,
    display_liability_positive BOOLEAN NOT NULL DEFAULT FALSE,
    apy_minor BIGINT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS tracking_account_details (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    polarity TEXT NOT NULL DEFAULT 'ASSET',
    source TEXT,
    apy_minor BIGINT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS investment_account_details (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    self_managed BOOLEAN NOT NULL,
    tax_treatment TEXT NOT NULL DEFAULT 'TAXABLE_BROKERAGE',
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS loan_details (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    original_amount_minor BIGINT,
    origination_date DATE,
    rate_minor BIGINT,
    status TEXT DEFAULT 'IN_REPAYMENT',
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS loan_balance_snapshots (
    row_id UUID PRIMARY KEY,
    snapshot_id UUID NOT NULL,
    account_id UUID NOT NULL,
    effective_date DATE NOT NULL,
    principal_balance_minor BIGINT NOT NULL,
    accrued_interest_minor BIGINT,
    escrow_balance_minor BIGINT NOT NULL DEFAULT 0,
    unapplied_credit_minor BIGINT NOT NULL DEFAULT 0,
    attributed_payment_minor BIGINT NOT NULL DEFAULT 0,
    principal_reduction_minor BIGINT NOT NULL DEFAULT 0,
    unknown_nonprincipal_minor BIGINT NOT NULL DEFAULT 0,
    notes TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS loan_transaction_attributions (
    row_id UUID PRIMARY KEY,
    attribution_id UUID NOT NULL,
    transaction_id UUID NOT NULL,
    loan_account_id UUID NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS tangible_asset_valuations (
    row_id UUID PRIMARY KEY,
    valuation_id UUID NOT NULL,
    account_id UUID NOT NULL,
    effective_date DATE NOT NULL,
    amount_minor BIGINT NOT NULL,
    source TEXT,
    notes TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS account_budget_links (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    category_id UUID NOT NULL,
    link_behavior TEXT NOT NULL,
    derivation_method TEXT NOT NULL DEFAULT 'TRANSFER_IN_ONLY',
    effective_date DATE NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS investment_positions (
    row_id UUID PRIMARY KEY,
    position_id UUID NOT NULL,
    account_id UUID NOT NULL,
    ticker TEXT NOT NULL,
    effective_date DATE NOT NULL,
    quantity_micros BIGINT NOT NULL,
    average_basis_minor BIGINT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS investment_cash_snapshots (
    row_id UUID PRIMARY KEY,
    snapshot_id UUID NOT NULL,
    account_id UUID NOT NULL,
    effective_date DATE NOT NULL,
    cash_balance_minor BIGINT NOT NULL,
    notes TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS investment_price_snapshots (
    row_id UUID PRIMARY KEY,
    snapshot_id UUID NOT NULL,
    account_id UUID,
    ticker TEXT NOT NULL,
    effective_date DATE NOT NULL,
    price_minor BIGINT NOT NULL,
    source TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS category_groups (
    row_id UUID PRIMARY KEY,
    group_id UUID NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_deletable BOOLEAN NOT NULL DEFAULT TRUE,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS categories (
    row_id UUID PRIMARY KEY,
    category_id UUID NOT NULL,
    group_id UUID NOT NULL,
    name TEXT NOT NULL,
    category_kind TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    target_amount_minor BIGINT,
    due_date_rule TEXT,
    goal_type TEXT,
    goal_amount_minor BIGINT,
    goal_frequency TEXT,
    goal_due_date DATE,
    metadata JSON,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS budget_buckets (
    row_id UUID PRIMARY KEY,
    bucket_id UUID NOT NULL,
    bucket_type TEXT NOT NULL,
    category_id UUID,
    is_allocatable BOOLEAN NOT NULL,
    is_deletable BOOLEAN NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE IF NOT EXISTS transactions (
    row_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    transfer_id UUID,
    date DATE NOT NULL,
    account_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    category_id UUID,
    system_category TEXT,
    status TEXT NOT NULL,
    memo TEXT,
    entry_order INTEGER NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (
        NOT (category_id IS NOT NULL AND system_category IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS allocations (
    row_id UUID PRIMARY KEY,
    allocation_id UUID NOT NULL,
    date DATE NOT NULL,
    from_bucket_id UUID NOT NULL,
    to_bucket_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    memo TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (amount_minor > 0),
    CHECK (from_bucket_id <> to_bucket_id)
);

CREATE TABLE IF NOT EXISTS net_worth_valuations (
    row_id UUID PRIMARY KEY,
    valuation_id UUID NOT NULL,
    account_id UUID,
    raw_name TEXT NOT NULL,
    effective_date DATE NOT NULL,
    amount_minor BIGINT NOT NULL,
    notes TEXT,
    metadata JSON,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE OR REPLACE VIEW current_accounts AS
SELECT * FROM accounts WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_budget_account_settings AS
SELECT * FROM budget_account_settings WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_tracking_account_details AS
SELECT * FROM tracking_account_details WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_investment_account_details AS
SELECT * FROM investment_account_details WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_loan_details AS
SELECT * FROM loan_details WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_loan_balance_snapshots AS
SELECT * FROM loan_balance_snapshots WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_loan_transaction_attributions AS
SELECT * FROM loan_transaction_attributions WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_tangible_asset_valuations AS
SELECT * FROM tangible_asset_valuations WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_account_budget_links AS
SELECT * FROM account_budget_links WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_investment_positions AS
SELECT * FROM investment_positions WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_investment_cash_snapshots AS
SELECT * FROM investment_cash_snapshots WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_investment_price_snapshots AS
SELECT * FROM investment_price_snapshots WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_category_groups AS
SELECT * FROM category_groups WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_categories AS
SELECT * FROM categories WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_budget_buckets AS
SELECT * FROM budget_buckets WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_transactions AS
SELECT * FROM transactions WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_allocations AS
SELECT * FROM allocations WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';

CREATE OR REPLACE VIEW current_net_worth_valuations AS
SELECT * FROM net_worth_valuations WHERE valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00';
