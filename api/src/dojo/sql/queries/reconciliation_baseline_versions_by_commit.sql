SELECT
    refs.reconciliation_id,
    refs.transaction_id,
    refs.valid_from AS baseline_valid_from,
    refs.account_id AS baseline_account_id,
    refs.canonical_row_digest,
    t.row_id,
    t.date,
    t.account_id,
    t.amount_minor,
    t.category_id,
    t.system_category,
    t.status,
    t.memo,
    t.entry_order,
    t.record_order,
    t.valid_from,
    t.valid_to,
    t.created_at,
    t.created_by_user_id
FROM reconciliation_transaction_refs AS refs
LEFT JOIN transactions AS t
    ON t.transaction_id = refs.transaction_id
   AND t.valid_from = refs.valid_from
WHERE refs.reconciliation_id = ?
ORDER BY t.date DESC NULLS LAST, t.entry_order DESC NULLS LAST, refs.transaction_id
