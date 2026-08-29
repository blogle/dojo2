SELECT row_id, operation_id, transaction_id, leg_role,
       valid_from, valid_to, created_at, created_by_user_id
FROM current_transaction_operation_legs
WHERE operation_id = ?
ORDER BY leg_role, row_id;
