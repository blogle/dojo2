SELECT *
FROM current_loan_balance_snapshots
WHERE account_id = ? AND effective_date = ?
ORDER BY created_at DESC
LIMIT 1
