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
    },
    {
        'name': 'Donchian Breakout + Uptrend Swing',
        'slug': 'donchian-breakout-uptrend-swing',
        'category': 'Trend Following',
        'hypothesis': 'Trend-following breakout strategy that enters when price moves above the upper band while the longer-term trend is bullish.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'upper'}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
            {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 22},
            {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>=', 'value': 50}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'lower'}}}
        ], 'logical_operator': 'OR'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
    },
    {
        'name': 'SMA Cross + Uptrend Swing',
        'slug': 'sma-cross-uptrend-swing',
        'category': 'Trend Following',
        'hypothesis': 'Uses short-term SMA crossover inside a strong uptrend to capture swing moves.',
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
        'hypothesis': 'Buys oversold pullbacks during a larger bullish trend using stochastic momentum.',
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
        'hypothesis': 'Uses bullish MACD crossover aligned with a strong trend to enter swing trades.',
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
        'hypothesis': 'Captures volatility expansion moves inside a strong uptrend.',
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
        'hypothesis': 'Identifies rising bullish momentum before a full MACD crossover.',
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
        'name': 'SuperTrend + Ichimoku Span B Filter',
        'slug': 'supertrend-ichimoku-spanb-filter',
        'category': 'Trend Following',
        'hypothesis': 'Trend-following strategy using SAR and EMA alignment as a proxy for SuperTrend + Ichimoku confirmation.',
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
        'name': 'Stochastic Oversold + EMA Uptrend',
        'slug': 'stochastic-oversold-ema-uptrend',
        'category': 'Trend Following',
        'hypothesis': 'Captures bullish reversals from oversold stochastic levels while the trend remains positive.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 25},
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowd'}}},
            {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
            {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'STOCH', 'params': {'k': 14, 'd': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.02, 'take_profit': 0.03})
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
    },
    {
        'name': 'Revenue Per Share Strategy',
        'slug': 'revenue-per-share-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Fundamental screen that identifies companies generating high revenue per share with healthy revenue growth.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Promoter Shareholding Strategy',
        'slug': 'promoter-shareholding-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Selects companies where promoters hold a significant stake and are increasing ownership.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Revenue Growth & EBITDA Strategy',
        'slug': 'revenue-growth-ebitda-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Focuses on businesses with strong sales growth and improving operating profitability.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'ROI & Profitability Strategy',
        'slug': 'roi-profitability-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Filters for companies generating high returns on invested capital with consistent profitability.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'P/E Ratio & EPS Growth Strategy',
        'slug': 'pe-eps-growth-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Combines valuation and earnings growth for GARP-style screening.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'EPS & Revenue Growth Strategy',
        'slug': 'eps-revenue-growth-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Targets companies exhibiting strong earnings and sales growth simultaneously.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Dividend Per Share Strategy',
        'slug': 'dividend-per-share-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Screens for dividend-paying companies with meaningful shareholder returns.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Dividend CAGR Strategy',
        'slug': 'dividend-cagr-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Focuses on companies consistently increasing dividends over time.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Debt-to-Equity & ROE Strategy',
        'slug': 'debt-to-equity-roe-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Selects financially strong companies with low leverage and high shareholder returns.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'Book Value Per Share Strategy',
        'slug': 'book-value-per-share-strategy',
        'category': 'Fundamental',
        'hypothesis': 'Value-oriented screen identifying companies trading near intrinsic asset value.',
        'entry_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({})
    },
    {
        'name': 'CCI + WilliamsR Mean Reversion',
        'slug': 'cci-williamsr-mean-reversion',
        'category': 'Mean Reversion',
        'hypothesis': 'Mean-reversion strategy combining two oversold oscillators within an uptrend.',
        'entry_rules': json.dumps({'conditions': [
            {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '<', 'value': -100},
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -75},
            {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
        ], 'logical_operator': 'AND'}),
        'exit_rules': json.dumps({'conditions': [
            {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '>', 'value': 0},
            {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -25}
        ], 'logical_operator': 'AND'}),
        'risk_params': json.dumps({'stop_loss': 0.07, 'take_profit': 0.10})
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
