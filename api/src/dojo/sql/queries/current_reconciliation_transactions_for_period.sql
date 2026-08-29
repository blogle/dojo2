SELECT * FROM current_transactions
WHERE account_id = ? AND date >= ? AND date <= ?
ORDER BY date, entry_order
