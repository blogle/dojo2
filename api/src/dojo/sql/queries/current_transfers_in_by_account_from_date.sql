SELECT
    t.account_id,
    t.amount_minor,
    t.date
FROM current_transactions t
WHERE t.account_id = ?
  AND t.system_category = 'TX_ACCOUNT_TRANSFER'
  AND t.amount_minor > 0
  AND t.date >= ?
