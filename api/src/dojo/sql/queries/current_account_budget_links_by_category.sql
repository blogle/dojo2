SELECT
    abl.account_id,
    abl.category_id,
    abl.link_behavior,
    abl.derivation_method,
    abl.effective_date
FROM current_account_budget_links abl
WHERE abl.category_id = ?
