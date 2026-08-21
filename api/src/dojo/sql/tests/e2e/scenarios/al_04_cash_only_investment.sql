INSERT INTO accounts (
    row_id, account_id, account_class, name, institution, account_number_last4,
    is_hidden, is_active, metadata, valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000401',
    '00000000-0000-0000-0000-000000000401',
    'INVESTMENT', 'Cash brokerage', 'Fidelity', NULL, FALSE, TRUE, NULL,
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
