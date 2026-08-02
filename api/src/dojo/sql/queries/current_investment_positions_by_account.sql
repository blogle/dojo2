SELECT
    position_id,
    account_id,
    ticker,
    effective_date,
    quantity_micros,
    average_basis_minor
FROM current_investment_positions
WHERE account_id = ?
ORDER BY effective_date DESC, ticker
