SELECT COUNT(*) AS cnt
FROM current_transactions
WHERE (category_id IS NULL OR category_id NOT IN ({category_placeholders}))
