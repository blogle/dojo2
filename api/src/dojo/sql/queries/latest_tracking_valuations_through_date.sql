SELECT * EXCLUDE (value_rank)
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY effective_date DESC, created_at DESC
        ) AS value_rank
    FROM current_net_worth_valuations
    WHERE account_id IS NOT NULL AND effective_date <= ?
)
WHERE value_rank = 1
