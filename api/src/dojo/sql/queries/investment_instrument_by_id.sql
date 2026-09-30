SELECT instrument_id, symbol, name, is_cash_equivalent
FROM investment_instruments
WHERE instrument_id = ?
