SELECT column_name, data_type, is_nullable
FROM duckdb_columns()
WHERE table_name = ?
ORDER BY column_index
