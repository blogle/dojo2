SELECT
    a.*, s.budget_account_type, s.linked_payment_category_id, s.display_liability_positive
FROM current_accounts a
LEFT JOIN current_budget_account_settings s ON s.account_id = a.account_id
ORDER BY a.name
