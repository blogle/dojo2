SELECT
    p.position_id,
    p.account_id,
    p.instrument_id,
    i.symbol,
    i.symbol AS ticker,
    i.name AS instrument_name,
    i.is_cash_equivalent,
    p.effective_date,
    p.quantity_micros,
    p.total_cost_basis_minor
FROM current_investment_positions p
JOIN investment_instruments i USING (instrument_id)
WHERE p.account_id = ?
ORDER BY p.effective_date DESC, i.symbol NULLS LAST, p.instrument_id
