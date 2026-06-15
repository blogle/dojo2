SELECT amount_minor
FROM current_transactions
WHERE account_id = ? AND system_category = ? AND amount_minor > 0
