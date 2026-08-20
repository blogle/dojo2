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
    l.rate_type AS loan_rate_type,
    l.scheduled_principal_interest_minor AS loan_scheduled_principal_interest_minor,
    l.payment_frequency AS loan_payment_frequency,
    l.next_payment_date AS loan_next_payment_date,
    l.maturity_date AS loan_maturity_date,
    l.remaining_term_months AS loan_remaining_term_months,
    l.recurring_extra_principal_minor AS loan_recurring_extra_principal_minor,
    l.status AS loan_status
FROM current_accounts a
LEFT JOIN current_budget_account_settings s ON s.account_id = a.account_id
LEFT JOIN current_tracking_account_details t ON t.account_id = a.account_id
LEFT JOIN current_investment_account_details i ON i.account_id = a.account_id
LEFT JOIN current_loan_details l ON l.account_id = a.account_id
ORDER BY a.name
