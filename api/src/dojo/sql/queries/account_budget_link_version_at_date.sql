SELECT row_id FROM account_budget_links
WHERE account_id = ? AND effective_date <= ? AND valid_from <= ? AND valid_to > ?
