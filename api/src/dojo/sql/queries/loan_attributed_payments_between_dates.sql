SELECT COALESCE(SUM(ABS(t.amount_minor)), 0) AS payment_minor
FROM current_loan_transaction_attributions attribution
JOIN current_transactions t ON t.transaction_id = attribution.transaction_id
WHERE attribution.loan_account_id = ?
  AND t.status = 'CLEARED'
  AND t.date > ?
  AND t.date <= ?
