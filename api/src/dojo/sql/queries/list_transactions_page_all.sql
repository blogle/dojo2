SELECT *
FROM current_transactions
ORDER BY {sort_expression}, created_at DESC, transaction_id DESC
LIMIT ? OFFSET ?
