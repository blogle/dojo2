SELECT operation_id, operation_kind, origin, client_operation_id,
       request_fingerprint, created_at, created_by_user_id
FROM transaction_operations
WHERE operation_id = ?;
