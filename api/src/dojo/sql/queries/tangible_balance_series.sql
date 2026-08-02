WITH valuations_in_range AS (
    SELECT effective_date AS day, amount_minor
    FROM current_tangible_asset_valuations
    WHERE account_id = ?
      AND effective_date >= CAST(? AS DATE)
      AND effective_date <= CAST(? AS DATE)
),
latest_before_start AS (
    SELECT amount_minor
    FROM current_tangible_asset_valuations
    WHERE account_id = ? AND effective_date < CAST(? AS DATE)
    ORDER BY effective_date DESC, created_at DESC
    LIMIT 1
),
spine AS (
    SELECT CAST(g.day AS DATE) AS day
    FROM generate_series(CAST(? AS DATE), CAST(? AS DATE), INTERVAL 1 DAY) AS g(day)
),
filled AS (
    SELECT
        s.day,
        COALESCE(
            (SELECT v.amount_minor FROM valuations_in_range v WHERE v.day <= s.day ORDER BY v.day DESC LIMIT 1),
            (SELECT lb.amount_minor FROM latest_before_start lb),
            0
        ) AS balance_minor
    FROM spine s
)
SELECT day AS date, balance_minor
FROM filled
ORDER BY day
