UPDATE account_budget_links
SET valid_to = ?
WHERE account_id = ?
  AND link_behavior = ?
  AND valid_to = TIMESTAMPTZ '9999-12-31 23:59:59+00'
