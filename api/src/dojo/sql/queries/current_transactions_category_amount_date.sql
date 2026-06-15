SELECT category_id, amount_minor, date
FROM current_transactions
WHERE category_id IS NOT NULL
