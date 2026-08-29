SELECT client_operation_id, command_kind, request_fingerprint, result, created_at
FROM financial_command_receipts
WHERE client_operation_id = ?;
