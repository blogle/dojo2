UPDATE {table}
SET valid_to = ?
WHERE {logical_column} = ?
  AND row_id = ?
  AND valid_to = TIMESTAMPTZ '{max_ts}'
RETURNING row_id
