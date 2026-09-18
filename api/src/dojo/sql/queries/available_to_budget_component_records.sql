SELECT
    id,
    kind,
    record_id,
    version,
    date,
    source_type,
    account_name,
    category_name,
    memo,
    contribution_minor
FROM (
    {contributions_query}
) AS contributions
WHERE component_key = ?
  AND group_key = ?
ORDER BY date, sort_entry_order, sort_record_order, sort_id
LIMIT ? OFFSET ?
