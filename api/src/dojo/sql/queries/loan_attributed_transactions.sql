SELECT
    t.*,
    account.name AS account_name,
    category.name AS category_name
FROM current_loan_transaction_attributions attribution
JOIN current_transactions t ON t.transaction_id = attribution.transaction_id
JOIN current_accounts account ON account.account_id = t.account_id
LEFT JOIN current_categories category ON category.category_id = t.category_id
WHERE attribution.loan_account_id = ?
ORDER BY t.date DESC, t.entry_order DESC
