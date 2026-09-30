SELECT p.*, i.symbol, i.name AS instrument_name
FROM current_investment_price_snapshots p
JOIN investment_instruments i USING (instrument_id)
WHERE (p.account_id = ? OR p.account_id IS NULL)
  AND p.instrument_id = ?
  AND p.effective_date = ?
ORDER BY
    CASE WHEN p.account_id = ? AND p.source = 'statement' THEN 0 ELSE 1 END,
    p.created_at DESC
LIMIT 1
