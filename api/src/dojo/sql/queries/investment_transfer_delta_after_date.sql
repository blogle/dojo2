SELECT COALESCE(SUM(amount_minor), 0) AS transfer_delta_minor
FROM current_transactions
WHERE account_id = ?
  AND system_category = 'TX_ACCOUNT_TRANSFER'
  AND status = 'CLEARED'
  AND date > ?
  AND date <= ?
