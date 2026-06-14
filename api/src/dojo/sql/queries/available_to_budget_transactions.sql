SELECT t.amount_minor, t.system_category
FROM current_transactions t
JOIN current_accounts a ON a.account_id = t.account_id
WHERE a.account_class = ? AND t.system_category IN (?, ?, ?)
