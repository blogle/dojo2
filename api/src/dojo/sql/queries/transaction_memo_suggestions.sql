WITH recent AS (
    SELECT memo, created_at
    FROM current_transactions
    WHERE memo <> '' AND {account_predicate}
    ORDER BY created_at DESC, entry_order DESC
    LIMIT 500
), ranked AS (
    SELECT
        memo,
        max(created_at) AS latest_created_at,
        max(jaro_winkler_similarity(lower(memo), lower(?))) AS similarity
    FROM recent
    GROUP BY memo
)
SELECT memo
FROM ranked
WHERE contains(lower(memo), lower(?)) OR similarity >= 0.72
ORDER BY similarity DESC, latest_created_at DESC
LIMIT ?
