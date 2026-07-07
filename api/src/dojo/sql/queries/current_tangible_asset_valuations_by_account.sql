SELECT
    valuation_id,
    account_id,
    effective_date,
    amount_minor,
    source,
    notes
FROM current_tangible_asset_valuations
WHERE account_id = ?
ORDER BY effective_date DESC
