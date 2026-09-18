SELECT
    COUNT(*) AS total,
    COALESCE(SUM(contribution_minor), 0) AS amount_minor
FROM (
    {contributions_query}
) AS contributions
WHERE component_key = ?
  AND group_key = ?
