SELECT
    position_id,
    account_id,
    ticker,
    quantity_minor,
    average_basis_minor
FROM current_investment_positions
WHERE account_id = ?
ORDER BY ticker
