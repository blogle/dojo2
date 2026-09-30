SELECT instrument_id, symbol, name, is_cash_equivalent
FROM investment_instruments
WHERE symbol = ?
ORDER BY created_at, instrument_id
LIMIT 1
