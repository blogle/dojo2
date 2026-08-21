SELECT
    transactions.transfer_id,
    transactions.transaction_id,
    transactions.account_id,
    accounts.name AS account_name
FROM current_transactions AS transactions
JOIN current_accounts AS accounts ON accounts.account_id = transactions.account_id
WHERE transactions.transfer_id IN ({transfer_placeholders})
