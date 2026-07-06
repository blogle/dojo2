SELECT *
FROM current_transactions
WHERE account_id NOT IN ({account_placeholders})
ORDER BY {sort_expression}, entry_order ASC
LIMIT ? OFFSET ?
