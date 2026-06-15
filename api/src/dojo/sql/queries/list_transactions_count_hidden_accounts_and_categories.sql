SELECT COUNT(*) AS cnt
FROM current_transactions
WHERE account_id NOT IN ({account_placeholders})
  AND (category_id IS NULL OR category_id NOT IN ({category_placeholders}))
