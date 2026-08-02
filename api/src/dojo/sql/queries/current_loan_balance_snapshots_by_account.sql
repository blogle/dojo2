SELECT
    snapshot_id,
    account_id,
    effective_date,
    principal_balance_minor,
    accrued_interest_minor,
    escrow_balance_minor,
    unapplied_credit_minor,
    attributed_payment_minor,
    principal_reduction_minor,
    unknown_nonprincipal_minor,
    notes
FROM current_loan_balance_snapshots
WHERE account_id = ?
ORDER BY effective_date DESC
