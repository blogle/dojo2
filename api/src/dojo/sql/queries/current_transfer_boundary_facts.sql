SELECT
    CAST(t.transaction_id AS VARCHAR) AS transaction_id,
    a.account_class,
    t.system_category,
    t.amount_minor,
    t.date AS effective_date,
    t.status
FROM current_transactions t
JOIN current_accounts a ON a.account_id = t.account_id
WHERE t.system_category = 'TX_ACCOUNT_TRANSFER'
  AND a.account_class IN ('BUDGET', 'INVESTMENT')
