WITH effective_link_intervals AS (
    {account_budget_link_effective_intervals}
), operation_accounts AS (
    SELECT
        legs.transaction_id,
        CAST(legs.operation_id AS VARCHAR) AS operation_id,
        operations.operation_kind,
        operations.origin,
        CAST(counterpart_transaction.account_id AS VARCHAR) AS counterparty_account_id,
        counterpart_account.name AS counterparty_account_name
    FROM current_transaction_operation_legs AS legs
    JOIN transaction_operations AS operations
      ON operations.operation_id = legs.operation_id
    JOIN current_transaction_operation_legs AS counterpart
      ON counterpart.operation_id = legs.operation_id
     AND counterpart.transaction_id <> legs.transaction_id
    JOIN current_transactions AS counterpart_transaction
      ON counterpart_transaction.transaction_id = counterpart.transaction_id
    JOIN current_accounts AS counterpart_account
      ON counterpart_account.account_id = counterpart_transaction.account_id
),
transaction_contributions AS (
    SELECT
        CASE t.system_category
            WHEN 'TX_AVAILABLE_TO_BUDGET' THEN 'transactions'
            WHEN 'TX_STARTING_BALANCE' THEN 'starting-balances'
            WHEN 'TX_BALANCE_ADJUSTMENT' THEN 'balance-adjustments'
        END AS component_key,
        CAST(t.account_id AS VARCHAR) AS group_key,
        a.name AS group_label,
        CONCAT('transaction:', CAST(t.transaction_id AS VARCHAR), ':', CAST(t.row_id AS VARCHAR)) AS id,
        'transaction' AS kind,
        CAST(t.transaction_id AS VARCHAR) AS record_id,
        CAST(t.row_id AS VARCHAR) AS version,
        t.date,
        t.system_category AS source_type,
        CAST(t.account_id AS VARCHAR) AS account_id,
        a.name AS account_name,
        CAST(NULL AS VARCHAR) AS category_id,
        CAST(NULL AS VARCHAR) AS category_name,
        oa.counterparty_account_id,
        oa.counterparty_account_name,
        t.memo,
        t.amount_minor AS contribution_minor,
        oa.operation_id,
        oa.operation_kind,
        oa.origin,
        t.entry_order AS sort_entry_order,
        COALESCE(t.record_order, 0) AS sort_record_order,
        CAST(t.row_id AS VARCHAR) AS sort_id
    FROM current_transactions AS t
    JOIN current_accounts AS a
      ON a.account_id = t.account_id
    LEFT JOIN operation_accounts AS oa
      ON oa.transaction_id = t.transaction_id
    WHERE a.account_class = 'BUDGET'
      AND t.system_category IN (
          'TX_AVAILABLE_TO_BUDGET',
          'TX_STARTING_BALANCE',
          'TX_BALANCE_ADJUSTMENT'
      )
      AND (
          t.system_category <> 'TX_STARTING_BALANCE'
          OR t.amount_minor > 0
      )
),
transfer_facts AS (
    SELECT
        t.transaction_id,
        CAST(t.row_id AS VARCHAR) AS version,
        CAST(t.account_id AS VARCHAR) AS account_id,
        a.account_class,
        a.name AS account_name,
        t.date,
        t.memo,
        t.entry_order,
        COALESCE(t.record_order, 0) AS record_order,
        t.amount_minor,
        CASE
            WHEN a.account_class = 'INVESTMENT'
             AND investment_link.category_id IS NOT NULL
             AND t.amount_minor < 0 THEN -t.amount_minor
            ELSE 0
        END AS contribution_minor
    FROM current_transactions AS t
    JOIN current_accounts AS a
      ON a.account_id = t.account_id
    LEFT JOIN LATERAL (
        SELECT link.category_id
        FROM effective_link_intervals AS link
        WHERE link.account_id = t.account_id
        AND link.link_behavior = 'INVESTMENT_CONTRIBUTION'
          AND link.derivation_method = 'TRANSFER_IN_ONLY'
          AND link.effective_date <= t.date
          AND (link.end_date IS NULL OR t.date < link.end_date)
        ORDER BY link.effective_date DESC
        LIMIT 1
    ) AS investment_link ON TRUE
    WHERE t.system_category = 'TX_ACCOUNT_TRANSFER'
      AND a.account_class IN ('BUDGET', 'INVESTMENT')
      AND t.date <= ?
),
transfer_contributions AS (
    SELECT
        'transfers' AS component_key,
        CASE
            WHEN oa.counterparty_account_id IS NOT NULL THEN
                CASE
                    WHEN tf.amount_minor < 0
                        THEN CONCAT(tf.account_id, ':', oa.counterparty_account_id)
                    ELSE CONCAT(oa.counterparty_account_id, ':', tf.account_id)
                END
            ELSE CONCAT(
                tf.account_id,
                CASE WHEN tf.amount_minor < 0 THEN ':out' ELSE ':in' END
            )
        END AS group_key,
        CASE
            WHEN oa.counterparty_account_id IS NOT NULL THEN
                CASE
                    WHEN tf.amount_minor < 0
                        THEN CONCAT(tf.account_name, ' -> ', oa.counterparty_account_name)
                    ELSE CONCAT(oa.counterparty_account_name, ' -> ', tf.account_name)
                END
            ELSE CONCAT(
                tf.account_name,
                CASE
                    WHEN tf.amount_minor < 0 THEN ' (outflow)' ELSE ' (inflow)'
                END
            )
        END AS group_label,
        CONCAT('transaction:', CAST(tf.transaction_id AS VARCHAR), ':', tf.version) AS id,
        'transfer' AS kind,
        CAST(tf.transaction_id AS VARCHAR) AS record_id,
        tf.version,
        tf.date,
        tf.account_class AS source_type,
        tf.account_id,
        tf.account_name,
        CAST(NULL AS VARCHAR) AS category_id,
        CAST(NULL AS VARCHAR) AS category_name,
        oa.counterparty_account_id,
        oa.counterparty_account_name,
        tf.memo,
        tf.contribution_minor,
        oa.operation_id,
        oa.operation_kind,
        oa.origin,
        tf.entry_order AS sort_entry_order,
        tf.record_order AS sort_record_order,
        tf.version AS sort_id
    FROM transfer_facts AS tf
    LEFT JOIN operation_accounts AS oa
      ON oa.transaction_id = tf.transaction_id
    WHERE tf.contribution_minor <> 0
),
allocation_contributions AS (
    SELECT
        'allocations' AS component_key,
        COALESCE(CAST(category.category_id AS VARCHAR), 'unknown-category') AS group_key,
        COALESCE(category.name, 'Unknown category') AS group_label,
        CONCAT('allocation:', CAST(allocation.allocation_id AS VARCHAR), ':', CAST(allocation.row_id AS VARCHAR)) AS id,
        'allocation' AS kind,
        CAST(allocation.allocation_id AS VARCHAR) AS record_id,
        CAST(allocation.row_id AS VARCHAR) AS version,
        allocation.date,
        'Category allocation' AS source_type,
        CAST(NULL AS VARCHAR) AS account_id,
        CAST(NULL AS VARCHAR) AS account_name,
        CAST(category.category_id AS VARCHAR) AS category_id,
        category.name AS category_name,
        CAST(NULL AS VARCHAR) AS counterparty_account_id,
        CAST(NULL AS VARCHAR) AS counterparty_account_name,
        allocation.memo,
        CASE
            WHEN allocation.from_bucket_id = '00000000-0000-0000-0000-00000000a7b0'
                THEN -allocation.amount_minor
            ELSE allocation.amount_minor
        END AS contribution_minor,
        CAST(NULL AS VARCHAR) AS operation_id,
        CAST(NULL AS VARCHAR) AS operation_kind,
        CAST(NULL AS VARCHAR) AS origin,
        0 AS sort_entry_order,
        0 AS sort_record_order,
        CAST(allocation.row_id AS VARCHAR) AS sort_id
    FROM current_allocations AS allocation
    LEFT JOIN current_budget_buckets AS bucket
      ON bucket.bucket_id = CASE
          WHEN allocation.from_bucket_id = '00000000-0000-0000-0000-00000000a7b0'
              THEN allocation.to_bucket_id
          ELSE allocation.from_bucket_id
      END
    LEFT JOIN current_categories AS category
      ON category.category_id = bucket.category_id
    WHERE allocation.from_bucket_id = '00000000-0000-0000-0000-00000000a7b0'
       OR allocation.to_bucket_id = '00000000-0000-0000-0000-00000000a7b0'
)
SELECT * FROM transaction_contributions
UNION ALL
SELECT * FROM transfer_contributions
UNION ALL
SELECT * FROM allocation_contributions
