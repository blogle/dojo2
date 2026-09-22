SELECT *
FROM current_transactions
WHERE transaction_id IN ({transaction_placeholders})
