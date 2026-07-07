SELECT
    snapshot_id,
    ticker,
    effective_date,
    price_minor,
    source
FROM current_investment_price_snapshots
WHERE ticker = ?
ORDER BY effective_date DESC
