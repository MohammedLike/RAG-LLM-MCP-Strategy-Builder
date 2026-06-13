-- Required for bulk OHLCV upserts (ingest_all_nse.py)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ohlcv_unique_pk'
    ) THEN
        ALTER TABLE ohlcv
            ADD CONSTRAINT ohlcv_unique_pk UNIQUE (time, symbol, resolution);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS ingest_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL DEFAULT 'nse_bse_daily',
    status TEXT NOT NULL DEFAULT 'pending',
    total_symbols INTEGER DEFAULT 0,
    completed_symbols INTEGER DEFAULT 0,
    failed_symbols JSONB DEFAULT '[]'::jsonb,
    last_symbol TEXT,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_ingest_jobs_status ON ingest_jobs (status, started_at DESC);
