CREATE TABLE loan_details (
    row_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    original_amount_minor BIGINT,
    origination_date DATE,
    rate_minor BIGINT,
    status TEXT DEFAULT 'IN_REPAYMENT',
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE loan_balance_snapshots (
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
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE investment_cash_snapshots (
    row_id UUID PRIMARY KEY,
    snapshot_id UUID NOT NULL,
    account_id UUID NOT NULL,
    effective_date DATE NOT NULL,
    cash_balance_minor BIGINT NOT NULL,
    notes TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE transactions (
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
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (NOT (category_id IS NOT NULL AND system_category IS NOT NULL))
);

INSERT INTO investment_cash_snapshots (
    row_id,
    snapshot_id,
    account_id,
    effective_date,
    cash_balance_minor,
    notes,
    valid_from,
    valid_to,
    created_at,
    created_by_user_id
) VALUES (
    '10000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000003',
    DATE '2026-01-01',
    10000,
    'Legacy cash statement',
    TIMESTAMPTZ '2026-01-01 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-01-01 12:00:00+00',
    NULL
);

INSERT INTO transactions (
    row_id,
    transaction_id,
    transfer_id,
    date,
    account_id,
    amount_minor,
    category_id,
    system_category,
    status,
    memo,
    entry_order,
    valid_from,
    valid_to,
    created_at,
    created_by_user_id
) VALUES (
    '20000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000002',
    NULL,
    DATE '2026-01-02',
    '20000000-0000-0000-0000-000000000003',
    -1000,
    NULL,
    'TX_ACCOUNT_TRANSFER',
    'CLEARED',
    'Legacy transfer',
    1,
    TIMESTAMPTZ '2026-01-02 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-01-02 12:00:00+00',
    NULL
);
