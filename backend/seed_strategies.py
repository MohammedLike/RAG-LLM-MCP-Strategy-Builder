import uuid
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://quant_user:quant_password@postgres:5432/quant_db'

strategies = [
    {
        'name': 'RSI Mean Reversion (Equity)',
        'slug': 'rsi-mean-reversion',
        'category': 'Equity',
        'hypothesis': 'Buy when RSI is oversold (<30) and exit when it reaches neutral (50) or overbought (70).',
        'entry_rules': json.dumps({'conditions': [{'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 30}], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [{'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 70}], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.02, 'take_profit': 0.05})
    },
    {
        'name': 'Golden Crossover (SMA)',
        'slug': 'golden-crossover',
        'category': 'Equity',
        'hypothesis': 'Classic trend following strategy where a fast SMA crosses above a slow SMA.',
        'entry_rules': json.dumps({'conditions': [{'indicator': 'SMA', 'params': {'timeperiod': 50}, 'operator': 'crosses_above', 'value': {'indicator': 'SMA', 'params': {'timeperiod': 200}}}], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [{'indicator': 'SMA', 'params': {'timeperiod': 50}, 'operator': 'crosses_below', 'value': {'indicator': 'SMA', 'params': {'timeperiod': 200}}}], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.05, 'take_profit': 0.15})
    },
    {
        'name': '9:20 Short Straddle (Options)',
        'slug': '920-short-straddle',
        'category': 'Options',
        'hypothesis': 'Capture high morning IV crush on BankNifty by selling both ATM Call and Put.',
        'entry_rules': json.dumps({'time': '09:20', 'instrument_type': 'OPTION', 'strike': 'ATM', 'option_type': 'STRADDLE', 'side': 'SELL'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.25, 'take_profit': 0.40})
    },
    {
        'name': 'Nifty Iron Condor',
        'slug': 'nifty-iron-condor',
        'category': 'Options',
        'hypothesis': 'Range-bound strategy selling OTM Call/Put and buying further OTM Call/Put as insurance.',
        'entry_rules': json.dumps({'instrument_type': 'OPTION', 'strikes': ['OTM+2', 'OTM+1', 'OTM-1', 'OTM-2'], 'option_type': 'IRON_CONDOR'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.15, 'take_profit': 0.30})
    },
    {
        'name': 'Supertrend Trend Rider',
        'slug': 'supertrend-rider',
        'category': 'Equity',
        'hypothesis': 'Ride the trend using Supertrend indicator. Buy on green, exit on red.',
        'entry_rules': json.dumps({'conditions': [{'indicator': 'SUPERTREND', 'params': {'period': 7, 'multiplier': 3}, 'operator': '==', 'value': 1}], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [{'indicator': 'SUPERTREND', 'params': {'period': 7, 'multiplier': 3}, 'operator': '==', 'value': -1}], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.03, 'take_profit': 0.10})
    }
]

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        for s in strategies:
            res = await session.execute(text("SELECT id FROM strategies WHERE slug = :slug"), {'slug': s['slug']})
            if not res.fetchone():
                await session.execute(
                    text("INSERT INTO strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) "
                         "VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
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
    asyncio.run(seed())
