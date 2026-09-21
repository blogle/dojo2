SELECT history.*
FROM transactions AS history
JOIN current_transactions AS current
  ON current.transaction_id = history.transaction_id
WHERE current.account_id = ?
ORDER BY history.transaction_id, history.valid_from
