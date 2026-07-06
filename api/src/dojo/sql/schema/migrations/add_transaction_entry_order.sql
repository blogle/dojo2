CREATE TABLE IF NOT EXISTS transactions__dojo_migrated (
    row_id UUID PRIMARY KEY,
    transaction_id UUID NOT NULL,
    date DATE NOT NULL,
    account_id UUID NOT NULL,
    amount_minor BIGINT NOT NULL,
    category_id UUID,
    system_category TEXT,
    status TEXT NOT NULL,
    memo TEXT,
    entry_order INTEGER NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (
        NOT (category_id IS NOT NULL AND system_category IS NOT NULL)
    )
);

INSERT INTO transactions__dojo_migrated
SELECT
    row_id,
    transaction_id,
    date,
    account_id,
    amount_minor,
    category_id,
    system_category,
    status,
    memo,
    ROW_NUMBER() OVER (ORDER BY created_at, row_id) AS entry_order,
    valid_from,
    valid_to,
    created_at,
    created_by_user_id
FROM transactions;

DROP TABLE transactions;
ALTER TABLE transactions__dojo_migrated RENAME TO transactions;
