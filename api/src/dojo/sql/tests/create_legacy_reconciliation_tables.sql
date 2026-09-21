CREATE TABLE reconciliation_commits (
    reconciliation_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    account_class TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    effective_date DATE NOT NULL,
    verified_at TIMESTAMPTZ,
    state TEXT NOT NULL,
    source_evidence_id UUID NOT NULL,
    source_evidence_digest TEXT NOT NULL,
    baseline_digest TEXT NOT NULL,
    source_ending_value_minor BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID
);

CREATE TABLE reconciliation_source_records (
    source_evidence_id UUID NOT NULL,
    source_record_id TEXT NOT NULL,
    transaction_id UUID,
    ordinal BIGINT NOT NULL,
    account_id UUID NOT NULL,
    posted_date DATE NOT NULL,
    cleared_date DATE,
    signed_amount_minor BIGINT NOT NULL,
    source_status TEXT NOT NULL,
    description TEXT NOT NULL,
    normalized_digest TEXT NOT NULL,
    raw_payload JSON,
    PRIMARY KEY (source_evidence_id, ordinal)
);

CREATE TABLE reconciliation_transaction_refs (
    reconciliation_id UUID NOT NULL,
    transaction_id UUID NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    account_id UUID NOT NULL,
    canonical_row_digest TEXT NOT NULL,
    PRIMARY KEY (reconciliation_id, transaction_id)
);
