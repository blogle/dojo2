SELECT
    CAST(t.row_id AS VARCHAR) AS version,
    CAST(t.transaction_id AS VARCHAR) AS transaction_id,
    CAST(t.account_id AS VARCHAR) AS account_id,
    a.name AS account_name,
    t.date,
    t.amount_minor,
    t.system_category,
    t.status,
    t.memo,
    t.entry_order,
    t.record_order
FROM current_transactions t
JOIN current_accounts a ON a.account_id = t.account_id
WHERE a.account_class = ?
  AND t.system_category IN (?, ?, ?)
ORDER BY t.date, t.entry_order, COALESCE(t.record_order, 0), t.row_id
