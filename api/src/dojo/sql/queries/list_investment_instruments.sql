SELECT instrument_id, symbol, name, is_cash_equivalent
FROM investment_instruments
ORDER BY symbol NULLS LAST, instrument_id
