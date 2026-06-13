import uuid
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

strategies = [
    {
        'name': 'Donchian Breakout + Uptrend Swing',
        'slug': 'donchian-breakout-uptrend-swing',
        'category': 'Trend Following',
        'hypothesis': 'Trend-following breakout strategy that enters when price breaks above the previous Donchian Channel high while the long-term trend remains bullish.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'upper'}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>=', 'value': 50}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'lower'}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'SMA Cross + Uptrend Swing',
        'slug': 'sma-cross-uptrend-swing',
        'category': 'Trend Following',
        'hypothesis': 'Uses short-term SMA crossover within a strong uptrend to capture swing moves.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'SMA', 'params': {'timeperiod': 9}, 'operator': '>', 'value': {'indicator': 'SMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'SMA', 'params': {'timeperiod': 9}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 45}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'SMA', 'params': {'timeperiod': 9}, 'operator': 'crosses_below', 'value': {'indicator': 'SMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'StochRSI Oversold + EMA Uptrend',
        'slug': 'stochrsi-oversold-ema-uptrend',
        'category': 'Momentum',
        'hypothesis': 'Buys oversold pullbacks during a larger bullish trend using Stochastic RSI.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 20},
            {'indicator': 'EMA', 'params': {'timeperiod': 8}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 21}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'ADX Trend + EMA50/200 + Parabolic SAR',
        'slug': 'adx-trend-ema-sar',
        'category': 'Trend Following',
        'hypothesis': 'Trend-strength strategy combining ADX, EMA alignment, and Parabolic SAR confirmation.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'PLUS_DI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': {'indicator': 'MINUS_DI', 'params': {'timeperiod': 14}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'SAR', 'params': {}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'SAR', 'params': {}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'Pivot Point Support + RSI Confirmation',
        'slug': 'pivot-support-rsi-confirmation',
        'category': 'Support & Resistance',
        'hypothesis': 'Buys near pivot support when RSI confirms bullish momentum.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'MIDPOINT', 'params': {}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'AVGPRICE', 'params': {}}},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 42},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'AVGPRICE', 'params': {}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'MACD Bull Cross + Uptrend Swing',
        'slug': 'macd-bull-cross-uptrend-swing',
        'category': 'Momentum',
        'hypothesis': 'Uses bullish MACD crossover aligned with an uptrend to enter swing trades.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}, 'operator': '>', 'value': {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9, 'output_index': 'signal'}}},
            {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9, 'output_index': 'hist'}, 'operator': '>', 'value': 0},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 20},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 45}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}, 'operator': '<', 'value': {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9, 'output_index': 'signal'}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'ATR Expansion + Uptrend Swing',
        'slug': 'atr-expansion-uptrend-swing',
        'category': 'Volatility',
        'hypothesis': 'Captures volatility expansion moves occurring in strong uptrends.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'ATR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 0},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 21}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 45},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 65}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 21}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'MFI Healthy + Uptrend Swing',
        'slug': 'mfi-healthy-uptrend-swing',
        'category': 'Momentum',
        'hypothesis': 'Uses Money Flow Index to find healthy accumulation during bullish trends.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 40},
            {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 60},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 20},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 48}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 75}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'MACD Histogram Rising + Uptrend Swing',
        'slug': 'macd-histogram-rising-uptrend-swing',
        'category': 'Momentum',
        'hypothesis': 'Identifies increasing bullish momentum before a full MACD crossover.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9, 'output_index': 'hist'}, 'operator': '>', 'value': 0},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 45}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'MACD', 'params': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9, 'output_index': 'hist'}, 'operator': '<', 'value': 0}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'CCI Oversold + EMA Uptrend',
        'slug': 'cci-oversold-ema-uptrend',
        'category': 'Momentum',
        'hypothesis': 'Buys oversold opportunities identified by CCI while maintaining a bullish long-term trend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '<', 'value': -100},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 35}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '>', 'value': 0}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'Bollinger Lower Touch + RSI Uptrend',
        'slug': 'bollinger-lower-touch-rsi-uptrend',
        'category': 'Mean Reversion',
        'hypothesis': 'Mean-reversion strategy that buys pullbacks to the lower Bollinger Band within an uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<=', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'lower'}}},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 42},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>=', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'middle'}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'MFI Wide Oversold + EMA Uptrend',
        'slug': 'mfi-wide-oversold-ema-uptrend',
        'category': 'Momentum',
        'hypothesis': 'Uses deeply oversold Money Flow Index readings to capture rebounds in an uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 35},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 65}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'SuperTrend + Ichimoku Span B Filter',
        'slug': 'supertrend-ichimoku-spanb-filter',
        'category': 'Trend Following',
        'hypothesis': 'Trend-following strategy requiring confirmation from both SuperTrend and Ichimoku Cloud structure.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'SAR', 'params': {}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'SAR', 'params': {}}}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'WilliamsR Deep Oversold + Uptrend',
        'slug': 'williamsr-deep-oversold-uptrend',
        'category': 'Momentum',
        'hypothesis': 'Buys extreme oversold conditions using Williams %R during an established uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -80},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 18}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -20}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'Stochastic Oversold + EMA Uptrend',
        'slug': 'stochastic-oversold-ema-uptrend',
        'category': 'Trend Following',
        'hypothesis': 'Captures bullish reversals from oversold stochastic levels while trend remains positive.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 25},
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowd'}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'RSI Pullback + EMA Uptrend',
        'slug': 'rsi-pullback-ema-uptrend',
        'category': 'Trend Following',
        'hypothesis': 'Buys temporary RSI weakness within a broader uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 40},
            {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 60}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.02, 'take_profit': 0.03})
    },
    {
        'name': 'Stochastic Oversold Pullback in Uptrend',
        'slug': 'stochastic-oversold-pullback-uptrend',
        'category': 'Trend Following',
        'hypothesis': 'Pullback strategy using stochastic oversold readings and bullish crossover in an uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 25},
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowd'}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'WilliamsR Oversold + RSI + ADX',
        'slug': 'williamsr-oversold-rsi-adx',
        'category': 'Momentum',
        'hypothesis': 'Combines oversold Williams %R with momentum and trend-strength filters.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -70},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 20},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 33}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -20}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    }
]

async def ensure_independent_strategy_table(engine):
    async with engine.begin() as conn:
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS independent_strategies (
                id UUID PRIMARY KEY,
                name VARCHAR NOT NULL,
                slug VARCHAR UNIQUE NOT NULL,
                category VARCHAR NOT NULL,
                hypothesis TEXT,
                entry_rules JSONB,
                exit_rules JSONB,
                risk_params JSONB,
                strategy_metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        ))

async def seed_independent_strategies():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    await ensure_independent_strategy_table(engine)

    async with async_session() as session:
        for s in strategies:
            res = await session.execute(text("SELECT id FROM independent_strategies WHERE slug = :slug"), {'slug': s['slug']})
            if res.fetchone():
                continue

            await session.execute(
                text("INSERT INTO independent_strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
                {
                    'id': uuid.uuid4(),
                    'name': s['name'],
                    'slug': s['slug'],
                    'category': s['category'],
                    'hypothesis': s['hypothesis'],
                    'entry_rules': s['entry_rules'],
                    'exit_rules': s['exit_rules'],
                    'risk_params': s['risk_params'],
                    'created_at': datetime.utcnow()
                }
            )
        await session.commit()

    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(seed_independent_strategies())
