SELECT
    p.*,
    i.symbol,
    i.symbol AS ticker,
    i.name AS instrument_name,
    i.is_cash_equivalent
FROM current_investment_positions p
JOIN investment_instruments i USING (instrument_id)
WHERE p.account_id = ? AND p.effective_date = ?
ORDER BY i.symbol NULLS LAST, p.instrument_id
