SELECT COUNT(*) AS cnt
FROM current_transactions
WHERE account_id NOT IN ({account_placeholders})
