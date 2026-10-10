SELECT
    p.row_id,
    p.position_id,
    p.instrument_id,
    p.quantity_micros,
    p.total_cost_basis_minor,
    p.effective_date,
    p.valid_from,
    i.symbol,
    i.name AS instrument_name
FROM current_investment_positions p
JOIN investment_instruments i USING (instrument_id)
WHERE p.account_id = ? AND p.effective_date <= ?
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY p.instrument_id ORDER BY p.effective_date DESC, p.valid_from DESC
) = 1
ORDER BY p.instrument_id
