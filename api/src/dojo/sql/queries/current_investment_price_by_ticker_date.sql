SELECT *
FROM current_investment_price_snapshots
WHERE (account_id = ? OR account_id IS NULL)
  AND ticker = ?
  AND effective_date = ?
ORDER BY
    CASE WHEN account_id = ? AND source = 'statement' THEN 0 ELSE 1 END,
    created_at DESC
LIMIT 1
