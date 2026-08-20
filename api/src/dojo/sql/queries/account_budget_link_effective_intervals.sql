WITH deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id, link_behavior, effective_date
            ORDER BY valid_from DESC
        ) AS correction_rank
    FROM account_budget_links
    WHERE derivation_method = 'TRANSFER_IN_ONLY'
), ordered AS (
    SELECT
        account_id,
        category_id,
        link_behavior,
        derivation_method,
        effective_date,
        LEAD(effective_date) OVER (
            PARTITION BY account_id, link_behavior
            ORDER BY effective_date
        ) AS end_date
    FROM deduplicated
    WHERE correction_rank = 1
)
SELECT *
FROM ordered
