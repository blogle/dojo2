SELECT *
FROM current_investment_positions
WHERE account_id = ? AND effective_date = ?
ORDER BY ticker
