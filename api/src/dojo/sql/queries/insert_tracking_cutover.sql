INSERT INTO tracking_cutovers (
    operation_id,
    predecessor_account_id,
    cutover_date,
    prior_value_minor,
    successor_total_minor,
    final_predecessor_valuation_id,
    request_fingerprint,
    created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
