SELECT
    CAST(t.row_id AS VARCHAR) AS version,
    CAST(t.transaction_id AS VARCHAR) AS transaction_id,
    CAST(t.account_id AS VARCHAR) AS account_id,
    a.account_class,
    a.name AS account_name,
    t.system_category,
    t.amount_minor,
    t.date AS effective_date,
    t.status,
    t.memo,
    t.entry_order,
    t.record_order
FROM current_transactions t
JOIN current_accounts a ON a.account_id = t.account_id
WHERE t.system_category = 'TX_ACCOUNT_TRANSFER'
  AND a.account_class IN ('BUDGET', 'INVESTMENT')
ORDER BY t.date, t.entry_order, COALESCE(t.record_order, 0), t.row_id
