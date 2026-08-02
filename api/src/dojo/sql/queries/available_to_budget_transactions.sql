SELECT t.amount_minor, t.system_category
FROM current_transactions t
JOIN current_accounts a ON a.account_id = t.account_id
WHERE a.account_class = ?
  AND (
      t.system_category IN (?, ?, ?)
      OR (
          t.system_category = ?
          AND t.amount_minor > 0
          AND t.transfer_id IS NOT NULL
          AND EXISTS (
              SELECT 1
              FROM current_transactions counterpart
              JOIN current_accounts counterpart_account
                ON counterpart_account.account_id = counterpart.account_id
              WHERE counterpart.transfer_id = t.transfer_id
                AND counterpart.transaction_id <> t.transaction_id
                AND counterpart_account.account_class = ?
          )
      )
  )
