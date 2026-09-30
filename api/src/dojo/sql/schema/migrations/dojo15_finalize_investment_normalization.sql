-- Legacy facts have been copied into the canonical instrument-keyed tables.
-- Remove staging copies only after every deterministic insert completed.
DROP TABLE IF EXISTS investment_positions_dojo15_legacy;
DROP TABLE IF EXISTS investment_price_snapshots_dojo15_legacy;
