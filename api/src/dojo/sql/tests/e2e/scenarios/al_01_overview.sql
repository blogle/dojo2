INSERT INTO accounts (
    row_id, account_id, account_class, name, institution, account_number_last4,
    is_hidden, is_active, metadata, valid_from, valid_to, created_at, created_by_user_id
) VALUES
    (
        '00000000-0000-0000-0000-000000000201',
        '00000000-0000-0000-0000-000000000201',
        'TRACKING', 'Tracking asset', NULL, NULL, FALSE, TRUE, NULL,
        TIMESTAMPTZ '2026-02-15 12:00:00+00',
        TIMESTAMPTZ '9999-12-31 23:59:59+00',
        TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
    ),
    (
        '00000000-0000-0000-0000-000000000301',
        '00000000-0000-0000-0000-000000000301',
        'TANGIBLE_ASSET', 'Tangible asset', NULL, NULL, FALSE, TRUE, NULL,
        TIMESTAMPTZ '2026-02-15 12:00:00+00',
        TIMESTAMPTZ '9999-12-31 23:59:59+00',
        TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
    ),
    (
        '00000000-0000-0000-0000-000000000401',
        '00000000-0000-0000-0000-000000000401',
        'INVESTMENT', 'Investment', NULL, NULL, FALSE, TRUE, NULL,
        TIMESTAMPTZ '2026-02-15 12:00:00+00',
        TIMESTAMPTZ '9999-12-31 23:59:59+00',
        TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
    ),
    (
        '00000000-0000-0000-0000-000000000501',
        '00000000-0000-0000-0000-000000000501',
        'LOAN', 'Loan', NULL, NULL, FALSE, TRUE, NULL,
        TIMESTAMPTZ '2026-02-15 12:00:00+00',
        TIMESTAMPTZ '9999-12-31 23:59:59+00',
        TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
    );

INSERT INTO tracking_account_details (
    row_id, account_id, polarity, source, apy_minor,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000202',
    '00000000-0000-0000-0000-000000000201',
    'ASSET', 'e2e', NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO net_worth_valuations (
    row_id, valuation_id, account_id, raw_name, effective_date, amount_minor, notes,
    metadata, valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000203',
    '00000000-0000-0000-0000-000000000203',
    '00000000-0000-0000-0000-000000000201',
    'Tracking asset', DATE '2026-02-15', 50000000, NULL, NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);

INSERT INTO tangible_asset_valuations (
    row_id, valuation_id, account_id, effective_date, amount_minor, source, notes,
    valid_from, valid_to, created_at, created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000302',
    '00000000-0000-0000-0000-000000000302',
    '00000000-0000-0000-0000-000000000301',
    DATE '2026-02-15', 2500000, 'e2e', '',
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
    DATE '2026-02-15', 1200000, 2, NULL,
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
    20000000, DATE '2026-02-15', 0, 'FIXED', 1, 'MONTHLY',
    DATE '2026-03-15', DATE '2036-02-15', 120, 0, 'IN_REPAYMENT',
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
    DATE '2026-02-15', 20000000, NULL, 400000, NULL, NULL, NULL, 0, 0, 0, NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00', NULL
);
