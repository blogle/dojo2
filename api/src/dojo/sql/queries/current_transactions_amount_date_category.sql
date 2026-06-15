SELECT amount_minor, date, category_id
FROM current_transactions
WHERE category_id IS NOT NULL
