SELECT
    snapshot_id,
    account_id,
    effective_date,
    cash_balance_minor,
    notes
FROM current_investment_cash_snapshots
WHERE account_id = ?
ORDER BY effective_date DESC
