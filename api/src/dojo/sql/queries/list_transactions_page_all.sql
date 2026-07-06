SELECT *
FROM current_transactions
ORDER BY {sort_expression}, entry_order ASC
LIMIT ? OFFSET ?
