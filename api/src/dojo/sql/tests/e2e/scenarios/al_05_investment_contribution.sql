UPDATE categories
SET name = 'Investment Contributions'
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
    150000,
    'Fund investment contribution',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO accounts (
    row_id, account_id, account_class, name, institution, account_number_last4,
    is_hidden, is_active, metadata, valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000401',
    '00000000-0000-0000-0000-000000000401',
    'INVESTMENT', 'Brokerage', 'Fidelity', NULL, FALSE, TRUE, NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO investment_account_details (
    row_id, account_id, self_managed, tax_treatment,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000402',
    '00000000-0000-0000-0000-000000000401',
    TRUE, 'TAXABLE_BROKERAGE',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO investment_cash_snapshots (
    row_id, snapshot_id, account_id, effective_date, cash_balance_minor, record_order,
    notes, valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000403',
    '00000000-0000-0000-0000-000000000403',
    '00000000-0000-0000-0000-000000000401',
    DATE '2026-02-15', 1000000, 0, 'Opening statement',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO account_budget_links (
    row_id, account_id, category_id, link_behavior, derivation_method, effective_date,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000404',
    '00000000-0000-0000-0000-000000000401',
    '00000000-0000-0000-0000-000000000011',
    'INVESTMENT_CONTRIBUTION', 'TRANSFER_IN_ONLY', DATE '2026-02-01',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);
