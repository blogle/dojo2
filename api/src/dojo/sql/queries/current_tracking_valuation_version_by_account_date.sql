SELECT row_id, valuation_id, effective_date, amount_minor, valid_from
FROM current_net_worth_valuations
WHERE account_id = ? AND effective_date = ?
ORDER BY created_at DESC
LIMIT 1
