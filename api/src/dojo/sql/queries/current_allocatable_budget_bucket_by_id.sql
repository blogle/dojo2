SELECT bucket_id
FROM current_budget_buckets
WHERE bucket_id = ?
  AND is_allocatable = TRUE
