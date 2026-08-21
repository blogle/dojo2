UPDATE categories
SET name = 'Mortgage'
WHERE category_id = '00000000-0000-0000-0000-000000000011';

INSERT INTO budget_buckets (
    row_id, bucket_id, bucket_type, category_id, is_allocatable, is_deletable,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000012',
    '0043043f-118e-5879-8750-bef8ffcff57d',
    'BUCKET_CATEGORY',
    '00000000-0000-0000-0000-000000000011',
    TRUE, TRUE,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO allocations (
    row_id, allocation_id, date, from_bucket_id, to_bucket_id, amount_minor, memo,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000013',
    '00000000-0000-0000-0000-000000000013',
    DATE '2026-02-01',
    '00000000-0000-0000-0000-00000000a7b0',
    '0043043f-118e-5879-8750-bef8ffcff57d',
    500000,
    'Fund mortgage payment',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO accounts (
    row_id, account_id, account_class, name, institution, account_number_last4,
    is_hidden, is_active, metadata, valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000501',
    '00000000-0000-0000-0000-000000000501',
    'LOAN', 'Chase Mortgage', 'Chase', NULL, FALSE, TRUE, NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO loan_details (
    row_id, account_id, original_amount_minor, origination_date, rate_minor, rate_type,
    scheduled_principal_interest_minor, payment_frequency, next_payment_date, maturity_date,
    remaining_term_months, recurring_extra_principal_minor, status,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000502',
    '00000000-0000-0000-0000-000000000501',
    20000000, DATE '2025-01-01', 600, 'FIXED', 500000, 'MONTHLY',
    DATE '2026-03-15', DATE '2030-01-01', 48, 0, 'IN_REPAYMENT',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO loan_balance_snapshots (
    row_id, snapshot_id, account_id, effective_date, principal_balance_minor,
    accrued_interest_minor, escrow_balance_minor, unapplied_credit_minor,
    ytd_principal_paid_minor, ytd_interest_paid_minor, attributed_payment_minor,
    principal_reduction_minor, unknown_nonprincipal_minor, notes,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000503',
    '00000000-0000-0000-0000-000000000503',
    '00000000-0000-0000-0000-000000000501',
    DATE '2026-02-01', 20000000, NULL, 400000, NULL, NULL, NULL, 0, 0, 0,
    'Opening lender statement',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO account_budget_links (
    row_id, account_id, category_id, link_behavior, derivation_method, effective_date,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000504',
    '00000000-0000-0000-0000-000000000501',
    '00000000-0000-0000-0000-000000000011',
    'LOAN_PAYMENT', 'TRANSFER_IN_ONLY', DATE '2026-02-01',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);
