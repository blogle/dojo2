ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS rate_type TEXT;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS scheduled_principal_interest_minor BIGINT;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS payment_frequency TEXT;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS next_payment_date DATE;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS maturity_date DATE;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS remaining_term_months INTEGER;
ALTER TABLE loan_details ADD COLUMN IF NOT EXISTS recurring_extra_principal_minor BIGINT;

ALTER TABLE loan_balance_snapshots ADD COLUMN IF NOT EXISTS ytd_principal_paid_minor BIGINT;
ALTER TABLE loan_balance_snapshots ADD COLUMN IF NOT EXISTS ytd_interest_paid_minor BIGINT;
ALTER TABLE loan_balance_snapshots ALTER COLUMN unapplied_credit_minor DROP NOT NULL;
ALTER TABLE loan_balance_snapshots ALTER COLUMN unapplied_credit_minor DROP DEFAULT;

ALTER TABLE investment_cash_snapshots ADD COLUMN IF NOT EXISTS record_order BIGINT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS record_order BIGINT;

CREATE TEMP TABLE rich_account_event_order_migration AS
WITH events AS (
    SELECT 'cash' AS event_kind, row_id, valid_from
    FROM investment_cash_snapshots
    WHERE record_order IS NULL

    UNION ALL

    SELECT 'transaction' AS event_kind, row_id, valid_from
    FROM transactions
    WHERE record_order IS NULL
), ordered AS (
    SELECT
        event_kind,
        row_id,
        ROW_NUMBER() OVER (ORDER BY valid_from, event_kind, row_id)
            - COUNT(*) OVER () - 1 AS record_order
    FROM events
)
SELECT * FROM ordered;

UPDATE investment_cash_snapshots AS snapshots
SET record_order = migrated.record_order
FROM rich_account_event_order_migration AS migrated
WHERE migrated.event_kind = 'cash'
  AND migrated.row_id = snapshots.row_id;

UPDATE transactions AS transactions
SET record_order = migrated.record_order
FROM rich_account_event_order_migration AS migrated
WHERE migrated.event_kind = 'transaction'
  AND migrated.row_id = transactions.row_id;

DROP TABLE rich_account_event_order_migration;
