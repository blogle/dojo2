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
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL DEFAULT TIMESTAMPTZ '9999-12-31 23:59:59+00',
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (
        NOT (category_id IS NOT NULL AND system_category IS NOT NULL)
    )
);

INSERT INTO transactions__dojo_migrated SELECT * FROM transactions;
DROP TABLE transactions;
ALTER TABLE transactions__dojo_migrated RENAME TO transactions;
