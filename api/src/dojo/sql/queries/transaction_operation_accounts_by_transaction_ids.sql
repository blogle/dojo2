SELECT legs.transaction_id,
       legs.operation_id,
       operations.operation_kind,
       counterpart.transaction_id AS counterpart_transaction_id,
       counterpart_transaction.account_id AS counterpart_account_id,
       accounts.name AS account_name
FROM current_transaction_operation_legs AS legs
JOIN transaction_operations AS operations
  ON operations.operation_id = legs.operation_id
JOIN current_transaction_operation_legs AS counterpart
  ON counterpart.operation_id = legs.operation_id
 AND counterpart.transaction_id <> legs.transaction_id
JOIN current_transactions AS counterpart_transaction
  ON counterpart_transaction.transaction_id = counterpart.transaction_id
JOIN current_accounts AS accounts
  ON accounts.account_id = counterpart_transaction.account_id
WHERE legs.transaction_id IN ({transaction_placeholders})
