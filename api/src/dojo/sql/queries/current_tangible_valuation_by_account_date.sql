SELECT *
FROM current_tangible_asset_valuations
WHERE account_id = ? AND effective_date = ?
ORDER BY created_at DESC
LIMIT 1
