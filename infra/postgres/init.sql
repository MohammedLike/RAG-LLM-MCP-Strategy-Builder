-- ══════════════════════════════════════════════════════════════
--  Quant AI Agent — PostgreSQL Schema
--  Runs on first container startup via docker-entrypoint-initdb.d
-- ══════════════════════════════════════════════════════════════

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ──────────────────────────────────────
--  OHLCV — Historical price data
--  Hypertable for time-series efficiency
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS ohlcv (
    timestamp   TIMESTAMPTZ     NOT NULL,
    symbol      VARCHAR(30)     NOT NULL,
    interval    VARCHAR(10)     NOT NULL DEFAULT '1d',  -- 1m, 5m, 15m, 1h, 1d
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      BIGINT          NOT NULL DEFAULT 0,
    vwap        DOUBLE PRECISION,
    trades      INTEGER,

    -- Composite primary key for deduplication
    PRIMARY KEY (timestamp, symbol, interval)
);

-- Convert to TimescaleDB hypertable (partitioned by time, monthly chunks)
SELECT create_hypertable(
    'ohlcv',
    by_range('timestamp', INTERVAL '1 month'),
    if_not_exists => TRUE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time
    ON ohlcv (symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_interval
    ON ohlcv (symbol, interval, timestamp DESC);


-- ──────────────────────────────────────
--  Options Chain — Snapshot data
--  Stores options chain at each capture
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS options_chain (
    id              UUID            DEFAULT uuid_generate_v4() PRIMARY KEY,
    captured_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    symbol          VARCHAR(30)     NOT NULL,   -- NIFTY, BANKNIFTY
    expiry          DATE            NOT NULL,
    strike          DOUBLE PRECISION NOT NULL,
    option_type     VARCHAR(2)      NOT NULL,   -- CE, PE

    -- Market data
    ltp             DOUBLE PRECISION,
    bid             DOUBLE PRECISION,
    ask             DOUBLE PRECISION,
    open_interest   BIGINT          DEFAULT 0,
    oi_change       BIGINT          DEFAULT 0,
    volume          BIGINT          DEFAULT 0,

    -- Greeks (computed or from source)
    iv              DOUBLE PRECISION,   -- Implied volatility
    delta           DOUBLE PRECISION,
    gamma           DOUBLE PRECISION,
    theta           DOUBLE PRECISION,
    vega            DOUBLE PRECISION,

    -- Derived metrics
    pcr             DOUBLE PRECISION,   -- Put-Call Ratio at this strike
    underlying_ltp  DOUBLE PRECISION    -- Spot price when captured
);

-- Convert to hypertable
SELECT create_hypertable(
    'options_chain',
    by_range('captured_at', INTERVAL '1 week'),
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_options_symbol_expiry
    ON options_chain (symbol, expiry, strike, option_type);

CREATE INDEX IF NOT EXISTS idx_options_captured
    ON options_chain (symbol, captured_at DESC);


-- ──────────────────────────────────────
--  Strategies — Knowledge base
--  Stores strategy definitions + results
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategies (
    id              UUID            DEFAULT uuid_generate_v4() PRIMARY KEY,
    name            VARCHAR(200)    NOT NULL,
    slug            VARCHAR(200)    NOT NULL UNIQUE,
    category        VARCHAR(50)     NOT NULL,   -- options_selling, directional, hedging, event_based
    underlying      VARCHAR(30)[]   NOT NULL DEFAULT '{}',  -- Array: {NIFTY, BANKNIFTY}

    -- Strategy definition (JSON for flexibility)
    hypothesis      TEXT,
    entry_rules     JSONB           NOT NULL DEFAULT '{}',
    exit_rules      JSONB           NOT NULL DEFAULT '{}',
    risk_params     JSONB           NOT NULL DEFAULT '{}',
    market_conditions JSONB         DEFAULT '{}',

    -- Backtest results (structured JSON)
    backtest_results JSONB          DEFAULT '{}',

    -- Metadata
    notes           TEXT,
    tags            VARCHAR(50)[]   DEFAULT '{}',
    is_active       BOOLEAN         DEFAULT TRUE,
    version         INTEGER         DEFAULT 1,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategies_category
    ON strategies (category);

CREATE INDEX IF NOT EXISTS idx_strategies_slug
    ON strategies (slug);

CREATE INDEX IF NOT EXISTS idx_strategies_tags
    ON strategies USING GIN (tags);


-- ──────────────────────────────────────
--  Backtest Runs — Cached results
--  Stores individual backtest executions
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS backtest_runs (
    id              UUID            DEFAULT uuid_generate_v4() PRIMARY KEY,
    strategy_id     UUID            REFERENCES strategies(id) ON DELETE SET NULL,
    strategy_slug   VARCHAR(200),

    -- Input parameters
    symbol          VARCHAR(30)     NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE            NOT NULL,
    initial_capital DOUBLE PRECISION DEFAULT 1000000,
    params          JSONB           DEFAULT '{}',   -- Strategy-specific params

    -- Results
    metrics         JSONB           NOT NULL,       -- Sharpe, Sortino, MaxDD, etc.
    equity_curve    JSONB,                          -- Array of {date, value} points
    trade_log       JSONB,                          -- Array of individual trades

    -- Metadata
    execution_time_ms INTEGER,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backtest_strategy
    ON backtest_runs (strategy_id, created_at DESC);


-- ──────────────────────────────────────
--  Chat Sessions — Conversation memory
--  (Supplement to Redis — persistent log)
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    id              UUID            DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id      VARCHAR(100)    NOT NULL UNIQUE,
    title           VARCHAR(300),
    message_count   INTEGER         DEFAULT 0,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    last_active     TIMESTAMPTZ     DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id              UUID            DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id      VARCHAR(100)    NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role            VARCHAR(20)     NOT NULL,   -- user, assistant, system, tool
    content         TEXT            NOT NULL,
    tool_calls      JSONB,                      -- MCP tool invocations
    tool_results    JSONB,                      -- Tool return values
    tokens_used     INTEGER,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages (session_id, created_at);


-- ──────────────────────────────────────
--  Continuous Aggregates (materialized)
--  Pre-computed views for dashboard
-- ──────────────────────────────────────

-- Daily summary from intraday data
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    symbol,
    first(open, timestamp)          AS open,
    max(high)                       AS high,
    min(low)                        AS low,
    last(close, timestamp)          AS close,
    sum(volume)                     AS volume,
    count(*)                        AS num_candles
FROM ohlcv
WHERE interval = '1m' OR interval = '5m'
GROUP BY bucket, symbol
WITH NO DATA;

-- Refresh policy: update daily summary every hour
SELECT add_continuous_aggregate_policy('ohlcv_daily_summary',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists   => TRUE
);


-- ──────────────────────────────────────
--  Utility function: auto-update timestamp
-- ──────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ══════════════════════════════════════
--  Schema initialized successfully
-- ══════════════════════════════════════
