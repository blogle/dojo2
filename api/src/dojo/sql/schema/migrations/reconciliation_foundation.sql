CREATE TABLE IF NOT EXISTS reconciliation_evidence (
    evidence_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    entity_class TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    source_adapter TEXT NOT NULL,
    source_as_of TIMESTAMPTZ NOT NULL,
    normalized_payload JSON NOT NULL,
    normalized_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (entity_class IN ('BUDGET', 'INVESTMENT', 'LOAN', 'TRACKING', 'TANGIBLE_ASSET'))
);

CREATE TABLE IF NOT EXISTS reconciliation_evidence_records (
    evidence_id UUID NOT NULL,
    ordinal BIGINT NOT NULL,
    source_record_id TEXT,
    transaction_id UUID,
    posted_date DATE,
    cleared_date DATE,
    signed_amount_minor BIGINT,
    settlement_state TEXT,
    description TEXT NOT NULL DEFAULT '',
    normalized_payload JSON NOT NULL,
    raw_payload JSON,
    PRIMARY KEY (evidence_id, ordinal)
);

CREATE TABLE IF NOT EXISTS reconciliation_commits (
    reconciliation_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    entity_class TEXT NOT NULL,
    evidence_id UUID NOT NULL UNIQUE,
    baseline_digest TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    created_by_user_id UUID,
    CHECK (entity_class IN ('BUDGET', 'INVESTMENT', 'LOAN', 'TRACKING', 'TANGIBLE_ASSET'))
);

CREATE TABLE IF NOT EXISTS reconciliation_history (
    history_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,
    entity_class TEXT NOT NULL,
    event_type TEXT NOT NULL,
    reconciliation_id UUID NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    reason TEXT,
    metadata JSON,
    CHECK (event_type IN ('COMMITTED', 'VOID')),
    CHECK (entity_class IN ('BUDGET', 'INVESTMENT', 'LOAN', 'TRACKING', 'TANGIBLE_ASSET'))
);

INSERT INTO reconciliation_evidence (
    evidence_id, entity_id, entity_class, evidence_kind, source_adapter,
    source_as_of, normalized_payload, normalized_digest, created_at, created_by_user_id
)
SELECT
    c.source_evidence_id,
    c.account_id,
    c.account_class,
    c.source_kind,
    'legacy',
    CAST(c.effective_date AS TIMESTAMPTZ),
    json_object(
        'legacy_period_start', CAST(c.period_start AS VARCHAR),
        'legacy_period_end', CAST(c.period_end AS VARCHAR),
        'source_ending_value_minor', c.source_ending_value_minor
    ),
    c.source_evidence_digest,
    c.created_at,
    c.created_by_user_id
FROM reconciliation_commits_legacy c
WHERE c.state IN ('CURRENT', 'REOPENED')
ON CONFLICT DO NOTHING;

INSERT INTO reconciliation_evidence_records (
    evidence_id, ordinal, source_record_id, transaction_id, posted_date, cleared_date,
    signed_amount_minor, settlement_state, description, normalized_payload, raw_payload
)
SELECT
    r.source_evidence_id,
    r.ordinal,
    r.source_record_id,
    r.transaction_id,
    r.posted_date,
    r.cleared_date,
    r.signed_amount_minor,
    r.source_status,
    r.description,
    json_object(
        'source_record_id', r.source_record_id,
        'transaction_id', CAST(r.transaction_id AS VARCHAR),
        'posted_date', CAST(r.posted_date AS VARCHAR),
        'cleared_date', CAST(r.cleared_date AS VARCHAR),
        'signed_amount_minor', r.signed_amount_minor,
        'settlement_state', r.source_status,
        'description', r.description
    ),
    r.raw_payload
FROM reconciliation_source_records_legacy r
WHERE EXISTS (
    SELECT 1 FROM reconciliation_evidence e WHERE e.evidence_id = r.source_evidence_id
)
ON CONFLICT DO NOTHING;

INSERT INTO reconciliation_commits (
    reconciliation_id, entity_id, entity_class, evidence_id, baseline_digest,
    committed_at, created_by_user_id
)
SELECT
    c.reconciliation_id,
    c.account_id,
    c.account_class,
    c.source_evidence_id,
    c.baseline_digest,
    COALESCE(c.verified_at, c.created_at),
    c.created_by_user_id
FROM reconciliation_commits_legacy c
WHERE c.state IN ('CURRENT', 'REOPENED')
ON CONFLICT DO NOTHING;

INSERT INTO reconciliation_history (
    history_id, entity_id, entity_class, event_type, reconciliation_id,
    recorded_at, reason, metadata
)
SELECT
    uuid(),
    c.account_id,
    c.account_class,
    'COMMITTED',
    c.reconciliation_id,
    COALESCE(c.verified_at, c.created_at),
    'Migrated legacy reconciliation commit',
    json_object('legacy_state', c.state)
FROM reconciliation_commits_legacy c
WHERE c.state IN ('CURRENT', 'REOPENED')
ON CONFLICT DO NOTHING;

DELETE FROM reconciliation_transaction_refs refs
WHERE NOT EXISTS (
    SELECT 1 FROM reconciliation_commits c
    WHERE c.reconciliation_id = refs.reconciliation_id
);
