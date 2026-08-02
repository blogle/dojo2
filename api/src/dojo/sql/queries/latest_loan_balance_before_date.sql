SELECT *
FROM current_loan_balance_snapshots
WHERE account_id = ? AND effective_date < ?
ORDER BY effective_date DESC, created_at DESC
LIMIT 1
