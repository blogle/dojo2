WITH deduplicated_links AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id, link_behavior, effective_date
            ORDER BY valid_from DESC
        ) AS correction_rank
    FROM account_budget_links
    WHERE derivation_method = 'TRANSFER_IN_ONLY'
), link_intervals AS (
    SELECT
        account_id,
        category_id,
        effective_date,
        LEAD(effective_date) OVER (
            PARTITION BY account_id, link_behavior
            ORDER BY effective_date
        ) AS end_date
    FROM deduplicated_links
    WHERE correction_rank = 1
), activity AS (
    SELECT
        t.transaction_id AS activity_id,
        t.category_id,
        t.date,
        a.name AS account_name,
        t.amount_minor,
        t.status,
        t.memo,
        FALSE AS is_derived
    FROM current_transactions t
    JOIN current_accounts a ON a.account_id = t.account_id
    WHERE t.category_id IS NOT NULL

    UNION ALL

    SELECT
        t.transaction_id AS activity_id,
        l.category_id,
        t.date,
        a.name AS account_name,
        -t.amount_minor AS amount_minor,
        t.status,
        t.memo,
        TRUE AS is_derived
    FROM current_transactions t
    JOIN link_intervals l ON l.account_id = t.account_id
    JOIN current_accounts a ON a.account_id = t.account_id
    WHERE t.system_category = 'TX_ACCOUNT_TRANSFER'
      AND t.amount_minor > 0
      AND t.date >= l.effective_date
      AND (l.end_date IS NULL OR t.date < l.end_date)
)
SELECT *
FROM activity
ORDER BY date DESC, activity_id DESC
