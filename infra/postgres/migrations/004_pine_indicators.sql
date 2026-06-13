-- TradingView / Pine Script indicator catalog for AI generation
CREATE TABLE IF NOT EXISTS pine_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    pine_name TEXT NOT NULL,
    long_name TEXT,
    category TEXT NOT NULL DEFAULT 'Other',
    description TEXT,
    params JSONB DEFAULT '{}',
    inputs JSONB DEFAULT '[]',
    backtest_supported BOOLEAN NOT NULL DEFAULT false,
    source TEXT NOT NULL DEFAULT 'tradingview',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_pine_indicators_category ON pine_indicators (category);
CREATE INDEX IF NOT EXISTS ix_pine_indicators_backtest ON pine_indicators (backtest_supported) WHERE backtest_supported = true;
