SELECT *
FROM current_transactions
WHERE account_id = ?
ORDER BY date DESC, entry_order DESC, transaction_id
