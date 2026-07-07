SELECT
    valuation_id,
    account_id,
    effective_date,
    amount_minor,
    notes,
    metadata
FROM current_net_worth_valuations
WHERE account_id = ?
ORDER BY effective_date DESC
