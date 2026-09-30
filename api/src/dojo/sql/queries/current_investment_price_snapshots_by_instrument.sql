SELECT snapshot_id, instrument_id, account_id, effective_date, price_minor, source
FROM current_investment_price_snapshots
WHERE instrument_id = ?
ORDER BY effective_date DESC
