-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create Ticks table for high-frequency data
CREATE TABLE IF NOT EXISTS ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume INTEGER,
    side TEXT -- 'buy', 'sell', or NULL
);

-- Create hypertable for ticks
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_ticks_symbol_time ON ticks (symbol, time DESC);

-- Create OHLCV table
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT,
    resolution TEXT NOT NULL -- '1m', '5m', '1h', '1d'
);

-- Create hypertable for OHLCV
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol_res_time ON ohlcv (symbol, resolution, time DESC);

-- Upsert key for bulk ingest scripts
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ohlcv_unique_pk') THEN
        ALTER TABLE ohlcv ADD CONSTRAINT ohlcv_unique_pk UNIQUE (time, symbol, resolution);
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

-- Enable compression for tick and ohlcv data (crucial for 8 years of data)
ALTER TABLE ticks SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'symbol'
);

ALTER TABLE ohlcv SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'symbol'
);

-- Add compression policies (e.g., compress data older than 7 days)
SELECT add_compression_policy('ticks', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_compression_policy('ohlcv', INTERVAL '30 days', if_not_exists => TRUE);

-- Create options chain table
CREATE TABLE IF NOT EXISTS options_chain (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    expiry DATE NOT NULL,
    strike DOUBLE PRECISION NOT NULL,
    option_type TEXT NOT NULL, -- 'CE' or 'PE'
    oi BIGINT,
    volume BIGINT,
    iv DOUBLE PRECISION,
    ltp DOUBLE PRECISION,
    greeks_json JSONB
);

SELECT create_hypertable('options_chain', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_options_chain_query 
ON options_chain (symbol, expiry, strike, time DESC);

-- Create strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    hypothesis TEXT,
    entry_rules JSONB,
    exit_rules JSONB,
    risk_params JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_strategies_category ON strategies (category);

-- Create backtests table to store results
CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id),
    pine_script_id UUID,
    user_request_json JSONB,
    status TEXT DEFAULT 'pending',
    symbol TEXT,
    period TEXT,
    resolution TEXT,
    strategy_spec JSONB,
    strategy_label TEXT,
    source TEXT DEFAULT 'engine',
    metrics JSONB,
    equity_curve JSONB,
    trade_log JSONB,
    drawdown_series JSONB,
    monthly_returns JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_backtests_created ON backtests (started_at DESC);
CREATE INDEX IF NOT EXISTS ix_backtests_symbol ON backtests (symbol);

-- User-authored Pine Script strategies
CREATE TABLE IF NOT EXISTS pine_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'upload',
    pine_script TEXT NOT NULL,
    strategy_spec JSONB,
    symbol TEXT,
    period TEXT,
    resolution TEXT,
    prompt TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_pine_scripts_created ON pine_scripts (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_pine_scripts_source ON pine_scripts (source);

ALTER TABLE backtests
    DROP CONSTRAINT IF EXISTS backtests_pine_script_id_fkey;
ALTER TABLE backtests
    ADD CONSTRAINT backtests_pine_script_id_fkey
    FOREIGN KEY (pine_script_id) REFERENCES pine_scripts(id) ON DELETE SET NULL;
