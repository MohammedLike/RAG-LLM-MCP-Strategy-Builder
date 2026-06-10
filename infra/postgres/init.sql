-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create OHLCV table
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT
);

-- Create hypertable for OHLCV
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Create index on symbol and time
CREATE INDEX IF NOT EXISTS ix_ohlcv_symbol_time ON ohlcv (symbol, time DESC);

-- Create options chain table
CREATE TABLE IF NOT EXISTS options_chain (
    timestamp TIMESTAMPTZ NOT NULL,
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

-- Index for querying options chain
CREATE INDEX IF NOT EXISTS ix_options_chain_symbol_expiry_strike 
ON options_chain (symbol, expiry, strike);

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
    backtest_results JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_strategies_category ON strategies (category);
