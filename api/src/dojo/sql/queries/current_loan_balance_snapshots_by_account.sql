SELECT
    snapshot_id,
    account_id,
    effective_date,
    principal_balance_minor,
    accrued_interest_minor,
    notes
FROM current_loan_balance_snapshots
WHERE account_id = ?
ORDER BY effective_date DESC
