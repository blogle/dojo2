INSERT INTO import_batches (
    import_batch_id,
    spreadsheet_id,
    spreadsheet_title,
    imported_at,
    cutover_at,
    summary
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'e2e-acceptance',
    'E2E acceptance',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    '{}'
);

INSERT INTO category_groups (
    row_id,
    group_id,
    name,
    sort_order,
    is_system,
    is_deletable,
    is_hidden,
    valid_from,
    valid_to,
    created_at,
    created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000010',
    '00000000-0000-0000-0000-000000000010',
    'E2E categories',
    1,
    FALSE,
    TRUE,
    FALSE,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    NULL
);

INSERT INTO categories (
    row_id,
    category_id,
    group_id,
    name,
    category_kind,
    sort_order,
    is_hidden,
    is_active,
    target_amount_minor,
    due_date_rule,
    goal_type,
    goal_amount_minor,
    goal_frequency,
    goal_due_date,
    metadata,
    valid_from,
    valid_to,
    created_at,
    created_by_user_id
) VALUES (
    '00000000-0000-0000-0000-000000000011',
    '00000000-0000-0000-0000-000000000011',
    '00000000-0000-0000-0000-000000000010',
    'E2E category',
    'STANDARD',
    1,
    FALSE,
    TRUE,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    TIMESTAMPTZ '2026-02-15 12:00:00+00',
    NULL
);
