SELECT
    (SELECT COUNT(*) FROM investment_cash_snapshots WHERE record_order IS NULL)
        AS cash_snapshot_count,
    (SELECT COUNT(*) FROM transactions WHERE record_order IS NULL)
        AS transaction_count
