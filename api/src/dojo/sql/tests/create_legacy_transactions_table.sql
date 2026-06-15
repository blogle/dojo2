CREATE TABLE transactions (
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
    valid_to TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (
        (category_id IS NOT NULL AND system_category IS NULL)
        OR
        (category_id IS NULL AND system_category IS NOT NULL)
    )
)
