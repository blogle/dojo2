SELECT bucket_id
FROM current_budget_buckets
WHERE category_id = ?
  AND bucket_type = 'BUCKET_CATEGORY'
  AND is_allocatable = TRUE;
