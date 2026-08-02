SELECT
    account_id,
    category_id,
    link_behavior,
    derivation_method,
    effective_date
FROM current_account_budget_links
WHERE account_id = ?
ORDER BY link_behavior
