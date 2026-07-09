SELECT *
FROM current_transactions
WHERE {filter_clause}
ORDER BY {sort_expression}, entry_order ASC
LIMIT ? OFFSET ?
