SELECT row_id
FROM {table}
WHERE {logical_column} = ?
  AND row_id = ?
  AND valid_to = TIMESTAMPTZ '{max_ts}'
