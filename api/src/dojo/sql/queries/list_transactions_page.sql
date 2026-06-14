SELECT *
FROM current_transactions
{where_clause}
ORDER BY {sort_expression}, created_at DESC, transaction_id DESC
LIMIT ? OFFSET ?
