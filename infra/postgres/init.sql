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

-- Create backtests table to store results
CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id),
    user_request_json JSONB, -- The original AI/User request
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    metrics JSONB, -- Sharpe, Sortino, MaxDD, etc.
    equity_curve JSONB, -- Time-series of portfolio value
    trade_log JSONB, -- List of all executed trades
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

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
