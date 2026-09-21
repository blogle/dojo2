SELECT history.*
FROM transactions AS history
JOIN current_transactions AS current
  ON current.transaction_id = history.transaction_id
LEFT JOIN reconciliation_transaction_refs AS refs
  ON refs.reconciliation_id = ?
 AND refs.transaction_id = history.transaction_id
WHERE current.account_id = ?
  AND refs.transaction_id IS NULL
ORDER BY history.transaction_id, history.valid_from
