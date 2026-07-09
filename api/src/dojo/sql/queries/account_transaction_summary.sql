WITH bounds AS (
    SELECT CAST(? AS DATE) AS start_date, CAST(? AS DATE) AS end_date, ? AS account_id
),
agg AS (
    SELECT
        COALESCE(SUM(CASE WHEN t.amount_minor > 0 THEN t.amount_minor ELSE 0 END), 0) AS inflow_minor,
        COALESCE(SUM(CASE WHEN t.amount_minor < 0 THEN t.amount_minor ELSE 0 END), 0) AS outflow_minor,
        COALESCE(SUM(t.amount_minor), 0) AS net_flow_minor,
        COUNT(*) AS transaction_count
    FROM current_transactions t
    WHERE t.account_id = (SELECT account_id FROM bounds)
      AND t.date >= (SELECT start_date FROM bounds)
      AND t.date <= (SELECT end_date FROM bounds)
),
total AS (
    SELECT COALESCE(SUM(t.amount_minor), 0) AS all_time_minor
    FROM current_transactions t
    WHERE t.account_id = (SELECT account_id FROM bounds)
),
spine AS (
    SELECT CAST(g.day AS DATE) AS day
    FROM generate_series(
        (SELECT start_date FROM bounds),
        (SELECT end_date FROM bounds),
        INTERVAL 1 DAY
    ) AS g(day)
),
day_amounts AS (
    SELECT t.date, SUM(t.amount_minor) AS day_amount
    FROM current_transactions t
    WHERE t.account_id = (SELECT account_id FROM bounds)
    GROUP BY t.date
),
running AS (
    SELECT
        s.day,
        CAST(? AS BIGINT) - (SELECT all_time_minor FROM total)
            + COALESCE(SUM(da.day_amount) OVER (ORDER BY s.day ASC), 0) AS balance_minor
    FROM spine s
    LEFT JOIN day_amounts da ON da.date = s.day
)
SELECT
    (SELECT inflow_minor FROM agg) AS inflow_minor,
    (SELECT outflow_minor FROM agg) AS outflow_minor,
    (SELECT net_flow_minor FROM agg) AS net_flow_minor,
    (SELECT transaction_count FROM agg) AS transaction_count,
    CAST(ROUND(AVG(balance_minor)) AS BIGINT) AS average_daily_balance_minor
FROM running