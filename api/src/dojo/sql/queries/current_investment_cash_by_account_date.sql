SELECT *
FROM current_investment_cash_snapshots
WHERE account_id = ? AND effective_date = ?
ORDER BY created_at DESC
LIMIT 1
