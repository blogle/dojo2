WITH per_entry AS (
    SELECT
        t.date AS day,
        t.entry_order AS entry_order,
        CAST(? AS BIGINT) - COALESCE(
            SUM(t.amount_minor) OVER (
                ORDER BY t.date DESC, t.entry_order DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ), 0
        ) AS balance_minor
    FROM current_transactions t
    WHERE t.account_id = ?
),
daily AS (
    SELECT day, balance_minor
    FROM (
        SELECT day, balance_minor, entry_order,
               ROW_NUMBER() OVER (PARTITION BY day ORDER BY entry_order DESC) AS rn
        FROM per_entry
    ) ranked
    WHERE rn = 1
),
bucketed AS (
    SELECT
        CAST(date_trunc('{bucket}', day) AS DATE) AS bucket,
        day,
        balance_minor
    FROM daily
),
ranked_buckets AS (
    SELECT bucket, day, balance_minor,
           ROW_NUMBER() OVER (PARTITION BY bucket ORDER BY day DESC) AS rn
    FROM bucketed
)
SELECT bucket AS date, balance_minor
FROM ranked_buckets
WHERE rn = 1
  AND day >= CAST(? AS DATE)
  AND day <= CAST(? AS DATE)
ORDER BY bucket