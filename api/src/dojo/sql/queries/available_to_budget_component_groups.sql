SELECT
    component_key,
    group_key,
    group_label,
    SUM(contribution_minor) AS amount_minor,
    COUNT(*) AS record_count
FROM (
    {contributions_query}
) AS contributions
GROUP BY component_key, group_key, group_label
ORDER BY ABS(SUM(contribution_minor)) DESC, LOWER(group_label), group_key
