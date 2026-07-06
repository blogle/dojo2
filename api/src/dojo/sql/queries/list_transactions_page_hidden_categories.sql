SELECT *
FROM current_transactions
WHERE (category_id IS NULL OR category_id NOT IN ({category_placeholders}))
ORDER BY {sort_expression}, entry_order ASC
LIMIT ? OFFSET ?
