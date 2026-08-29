SELECT row_id FROM budget_account_settings
WHERE account_id = ? AND valid_from <= ? AND valid_to > ?
