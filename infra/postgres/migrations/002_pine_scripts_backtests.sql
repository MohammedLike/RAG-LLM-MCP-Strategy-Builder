-- Pine scripts authored/uploaded by users
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

-- Extend backtests table (base table created in init.sql)
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS pine_script_id UUID REFERENCES pine_scripts(id) ON DELETE SET NULL;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS symbol TEXT;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS period TEXT;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS resolution TEXT;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS strategy_spec JSONB;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS strategy_label TEXT;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'engine';
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS drawdown_series JSONB;
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS monthly_returns JSONB;

CREATE INDEX IF NOT EXISTS ix_backtests_created ON backtests (started_at DESC);
CREATE INDEX IF NOT EXISTS ix_backtests_symbol ON backtests (symbol);
CREATE INDEX IF NOT EXISTS ix_backtests_pine_script ON backtests (pine_script_id);
