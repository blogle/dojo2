SELECT
    c.predecessor_account_id,
    s.successor_account_id,
    c.cutover_date
FROM tracking_cutovers c
JOIN tracking_cutover_successors s ON s.operation_id = c.operation_id
