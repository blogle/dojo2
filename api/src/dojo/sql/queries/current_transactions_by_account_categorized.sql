SELECT amount_minor, system_category
FROM current_transactions
WHERE account_id = ? AND category_id IS NOT NULL
