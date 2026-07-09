SELECT status, COUNT(*) AS cnt
FROM current_transactions
WHERE {filter_clause}
GROUP BY status
