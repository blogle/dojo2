SELECT
    account_id,
    SUM(amount_minor) AS actual,
    SUM(CASE WHEN status = 'CLEARED' THEN amount_minor ELSE 0 END) AS cleared,
    SUM(CASE WHEN status = 'PENDING' THEN amount_minor ELSE 0 END) AS pending
FROM current_transactions
GROUP BY account_id
