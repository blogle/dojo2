SELECT *
FROM current_transactions
WHERE account_id NOT IN ({account_placeholders})
ORDER BY {sort_expression}, created_at DESC, transaction_id DESC
LIMIT ? OFFSET ?
