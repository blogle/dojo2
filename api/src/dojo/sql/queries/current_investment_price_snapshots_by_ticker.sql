SELECT
    p.snapshot_id,
    p.instrument_id,
    i.symbol,
    i.symbol AS ticker,
    p.account_id,
    p.effective_date,
    p.price_minor,
    p.source
FROM current_investment_price_snapshots p
JOIN investment_instruments i USING (instrument_id)
WHERE i.symbol = ?
ORDER BY p.effective_date DESC
