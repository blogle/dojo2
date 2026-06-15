UPDATE {table}
SET valid_to = ?
WHERE {logical_column} = ? AND valid_to = TIMESTAMPTZ '{max_ts}'
