SELECT
    COUNT(*) AS object_count
FROM information_schema.tables
WHERE table_schema = 'main'
