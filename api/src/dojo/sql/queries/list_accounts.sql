SELECT
    a.*,
    s.budget_account_type,
    s.display_liability_positive,
    s.apy_minor AS budget_apy_minor,
    t.polarity AS tracking_polarity,
    t.source AS tracking_source,
    t.apy_minor AS tracking_apy_minor,
    i.self_managed AS investment_self_managed,
    i.tax_treatment AS investment_tax_treatment,
    l.original_amount_minor AS loan_original_amount_minor,
    l.origination_date AS loan_origination_date,
    l.rate_minor AS loan_rate_minor,
    l.status AS loan_status
FROM current_accounts a
LEFT JOIN current_budget_account_settings s ON s.account_id = a.account_id
LEFT JOIN current_tracking_account_details t ON t.account_id = a.account_id
LEFT JOIN current_investment_account_details i ON i.account_id = a.account_id
LEFT JOIN current_loan_details l ON l.account_id = a.account_id
ORDER BY a.name
