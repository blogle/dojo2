WITH bounds AS (
    SELECT CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date, ? AS account_id
),
valuations_in_range AS (
    SELECT effective_date, amount_minor
    FROM current_tangible_asset_valuations
    WHERE account_id = (SELECT account_id FROM bounds)
      AND effective_date >= (SELECT start_date FROM bounds)
      AND effective_date <= (SELECT end_date FROM bounds)
    ORDER BY effective_date
),
latest_before_start AS (
    SELECT amount_minor
    FROM current_tangible_asset_valuations
    WHERE account_id = (SELECT account_id FROM bounds)
      AND effective_date < (SELECT start_date FROM bounds)
    ORDER BY effective_date DESC, created_at DESC
    LIMIT 1
),
spine AS (
    SELECT CAST(g.day AS DATE) AS day
    FROM generate_series(
        (SELECT start_date FROM bounds),
        (SELECT end_date FROM bounds),
        INTERVAL 1 DAY
    ) AS g(day)
),
filled AS (
    SELECT
        s.day,
        COALESCE(
            (SELECT v.amount_minor FROM valuations_in_range v WHERE v.effective_date <= s.day ORDER BY v.effective_date DESC LIMIT 1),
            (SELECT lb.amount_minor FROM latest_before_start lb),
            0
        ) AS balance_minor
    FROM spine s
),
daily_changes AS (
    SELECT
        day,
        balance_minor,
        balance_minor - LAG(balance_minor) OVER (ORDER BY day) AS day_change
    FROM filled
)
SELECT
    COALESCE(SUM(CASE WHEN day_change > 0 THEN day_change ELSE 0 END), 0) AS inflow_minor,
    COALESCE(SUM(CASE WHEN day_change < 0 THEN day_change ELSE 0 END), 0) AS outflow_minor,
    COALESCE(SUM(day_change), 0) AS net_flow_minor,
    COUNT(day_change) AS snapshot_count,
    CAST(ROUND(AVG(balance_minor)) AS BIGINT) AS average_daily_balance_minor
FROM daily_changes
