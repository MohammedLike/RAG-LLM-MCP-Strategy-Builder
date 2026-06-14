-- Unique key for options_chain upserts (idempotent daily ingest)
CREATE UNIQUE INDEX IF NOT EXISTS options_chain_unique_pk
ON options_chain (time, symbol, expiry, strike, option_type);
