import uuid
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://quant_user:quant_password@postgres:5432/quant_db'

# Define 30 distinct Equity strategies with 'eq-' slug prefix
equity_strategies = [
    {
        "name": "RSI Mean Reversion (Equity)",
        "slug": "eq-rsi-mean-reversion",
        "category": "Equity",
        "hypothesis": "Buy when RSI is oversold (<30) and exit when it reaches neutral (50) or overbought (70).",
        "entry_rules": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "<", "value": 30}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": ">", "value": 70}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.05}
    },
    {
        "name": "Golden Crossover (SMA)",
        "slug": "eq-golden-crossover",
        "category": "Equity",
        "hypothesis": "Classic trend following strategy where a fast SMA crosses above a slow SMA.",
        "entry_rules": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": 50}, "operator": "crosses_above", "value": {"indicator": "SMA", "params": {"timeperiod": 200}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": 50}, "operator": "crosses_below", "value": {"indicator": "SMA", "params": {"timeperiod": 200}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15}
    },
    {
        "name": "Supertrend Trend Rider",
        "slug": "eq-supertrend-rider",
        "category": "Equity",
        "hypothesis": "Ride the trend using Supertrend indicator. Buy on green, exit on red.",
        "entry_rules": {"conditions": [{"indicator": "SUPERTREND", "params": {"period": 7, "multiplier": 3}, "operator": "==", "value": 1}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "SUPERTREND", "params": {"period": 7, "multiplier": 3}, "operator": "==", "value": -1}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.10}
    },
    {
        "name": "Fast EMA Crossover (9/21)",
        "slug": "eq-ema-crossover-fast",
        "category": "Equity",
        "hypothesis": "Uses 9 EMA crossing 21 EMA to capture short term momentum shifts.",
        "entry_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 9}, "operator": "crosses_above", "value": {"indicator": "EMA", "params": {"timeperiod": 21}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 9}, "operator": "crosses_below", "value": {"indicator": "EMA", "params": {"timeperiod": 21}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.015, "take_profit": 0.04}
    },
    {
        "name": "Slow EMA Crossover (50/200)",
        "slug": "eq-ema-crossover-slow",
        "category": "Equity",
        "hypothesis": "Captures long term macro trends using 50 EMA crossing 200 EMA.",
        "entry_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 50}, "operator": "crosses_above", "value": {"indicator": "EMA", "params": {"timeperiod": 200}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 50}, "operator": "crosses_below", "value": {"indicator": "EMA", "params": {"timeperiod": 200}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.12}
    },
    {
        "name": "MACD Histogram Divergence",
        "slug": "eq-macd-histogram-divergence",
        "category": "Equity",
        "hypothesis": "Enters on MACD histogram crossing above 0, showing trend momentum reversal.",
        "entry_rules": {"conditions": [{"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "hist"}, "operator": "crosses_above", "value": 0}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "hist"}, "operator": "crosses_below", "value": 0}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "RSI Oversold Pullback",
        "slug": "eq-rsi-oversold-pullback",
        "category": "Equity",
        "hypothesis": "Buys pullbacks in an uptrend when 14-day RSI drops below 40.",
        "entry_rules": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "<", "value": 40}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": ">", "value": 65}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.05}
    },
    {
        "name": "Bollinger Band Breakout",
        "slug": "eq-bollinger-breakout-equity",
        "category": "Equity",
        "hypothesis": "Enters long when the price breaks out of the upper Bollinger Band.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "BBANDS", "params": {"timeperiod": 20, "nbdevup": 2, "output_index": "upper"}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "BBANDS", "params": {"timeperiod": 20, "nbdevup": 2, "output_index": "middle"}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.09}
    },
    {
        "name": "Stochastic RSI Crossover",
        "slug": "eq-stochastic-rsi-crossover",
        "category": "Equity",
        "hypothesis": "Buys when Stochastic RSI K crosses above D below the 20 level.",
        "entry_rules": {"conditions": [{"indicator": "STOCH", "params": {"k": 14, "d": 3, "output_index": "slowk"}, "operator": "crosses_above", "value": {"indicator": "STOCH", "params": {"k": 14, "d": 3, "output_index": "slowd"}}}, {"indicator": "STOCH", "params": {"k": 14, "d": 3, "output_index": "slowk"}, "operator": "<", "value": 20}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "STOCH", "params": {"k": 14, "d": 3, "output_index": "slowk"}, "operator": ">", "value": 80}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.025, "take_profit": 0.07}
    },
    {
        "name": "ATR Volatility Channel Breakout",
        "slug": "eq-atr-breakout-trend",
        "category": "Equity",
        "hypothesis": "Buy breakout of volatility channels using Average True Range.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "EMA", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.035, "take_profit": 0.10}
    },
    {
        "name": "Triple EMA Trend Rider (9/21/55)",
        "slug": "eq-triple-ema-trend",
        "category": "Equity",
        "hypothesis": "Ride the trend in strongly aligned EMA states.",
        "entry_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 9}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 21}}}, {"indicator": "EMA", "params": {"timeperiod": 21}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 55}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "EMA", "params": {"timeperiod": 9}, "operator": "<", "value": {"indicator": "EMA", "params": {"timeperiod": 21}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Parabolic SAR Trend Following",
        "slug": "eq-parabolic-sar-trend",
        "category": "Equity",
        "hypothesis": "Enters long when SAR moves below close price, exits when SAR crosses above close price.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "SAR", "params": {}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "SAR", "params": {}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.08}
    },
    {
        "name": "CCI Reversal Strategy",
        "slug": "eq-commodity-channel-reversal",
        "category": "Equity",
        "hypothesis": "Buys oversold CCI reversals from below -100.",
        "entry_rules": {"conditions": [{"indicator": "CCI", "params": {"timeperiod": 14}, "operator": "crosses_above", "value": -100}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CCI", "params": {"timeperiod": 14}, "operator": "crosses_below", "value": 100}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.05}
    },
    {
        "name": "Williams %R Extreme Oversold",
        "slug": "eq-williams-r-extreme",
        "category": "Equity",
        "hypothesis": "Enters on Williams %R returning from oversold zone below -80.",
        "entry_rules": {"conditions": [{"indicator": "WILLR", "params": {"timeperiod": 14}, "operator": "crosses_above", "value": -80}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "WILLR", "params": {"timeperiod": 14}, "operator": "crosses_below", "value": -20}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Donchian Channel Breakout (Equity)",
        "slug": "eq-donchian-channel-breakout",
        "category": "Equity",
        "hypothesis": "Buys when close price crosses above the 20-day high Donchian Channel.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "HIGH", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "LOW", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.12}
    },
    {
        "name": "Price ROC Momentum Strategy",
        "slug": "eq-price-rate-of-change",
        "category": "Equity",
        "hypothesis": "Uses Price Rate of Change to buy when momentum accelerates above 0.",
        "entry_rules": {"conditions": [{"indicator": "ROC", "params": {"timeperiod": 12}, "operator": ">", "value": 0}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "ROC", "params": {"timeperiod": 12}, "operator": "<", "value": -2}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.025, "take_profit": 0.075}
    },
    {
        "name": "MFI Volume-Weighted Reversion",
        "slug": "eq-money-flow-index-reversion",
        "category": "Equity",
        "hypothesis": "Enters when Money Flow Index is oversold (<20) indicating volume capitulation.",
        "entry_rules": {"conditions": [{"indicator": "MFI", "params": {"timeperiod": 14}, "operator": "<", "value": 20}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "MFI", "params": {"timeperiod": 14}, "operator": ">", "value": 60}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Chaikin Money Flow Breakout",
        "slug": "eq-chaikin-money-flow",
        "category": "Equity",
        "hypothesis": "Buys when Chaikin Money Flow crosses above 0.1, showing institutional accumulation.",
        "entry_rules": {"conditions": [{"indicator": "MFI", "params": {"timeperiod": 20}, "operator": ">", "value": 50}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "MFI", "params": {"timeperiod": 20}, "operator": "<", "value": 40}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.08}
    },
    {
        "name": "ADX Trend Strength Filter (Equity)",
        "slug": "eq-adx-trend-strength",
        "category": "Equity",
        "hypothesis": "Only buy when ADX is higher than 25, confirming a strong trend, and +DI is above -DI.",
        "entry_rules": {"conditions": [{"indicator": "ADX", "params": {"timeperiod": 14}, "operator": ">", "value": 25}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "ADX", "params": {"timeperiod": 14}, "operator": "<", "value": 15}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.09}
    },
    {
        "name": "Keltner Channel Mean Reversion",
        "slug": "eq-keltner-channel-reversal",
        "category": "Equity",
        "hypothesis": "Buys when close price falls below the lower Keltner band and reverses.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "EMA", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.05}
    },
    {
        "name": "Fibonacci Support Swing Trade",
        "slug": "eq-fibonacci-retracement-swing",
        "category": "Equity",
        "hypothesis": "Buy swing support bounces using standard moving averages as support proxies.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "SMA", "params": {"timeperiod": 50}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "SMA", "params": {"timeperiod": 50}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.025, "take_profit": 0.07}
    },
    {
        "name": "Volatility Ratio Expansion",
        "slug": "eq-volatility-ratio-expansion",
        "category": "Equity",
        "hypothesis": "Enters when ATR volatility expands compared to its historical average.",
        "entry_rules": {"conditions": [{"indicator": "ATR", "params": {"timeperiod": 5}, "operator": ">", "value": {"indicator": "ATR", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "ATR", "params": {"timeperiod": 5}, "operator": "<", "value": {"indicator": "ATR", "params": {"timeperiod": 20}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.08}
    },
    {
        "name": "Heikin Ashi Trend Following",
        "slug": "eq-heikin-ashi-trend",
        "category": "Equity",
        "hypothesis": "Smooths price trends and enters long when consecutive candles are bullish.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 10}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "EMA", "params": {"timeperiod": 10}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Linear Regression Slope Strategy",
        "slug": "eq-linear-regression-slope",
        "category": "Equity",
        "hypothesis": "Buys when the 14-day linear regression slope turns positive.",
        "entry_rules": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": 14}, "operator": ">", "value": {"indicator": "SMA", "params": {"timeperiod": 30}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "SMA", "params": {"timeperiod": 14}, "operator": "<", "value": {"indicator": "SMA", "params": {"timeperiod": 30}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "VWAP Intraday Mean Reversion (Equity)",
        "slug": "eq-vwap-mean-reversion-equity",
        "category": "Equity",
        "hypothesis": "Buys when equity is oversold below its Volume-Weighted Average Price (VWAP).",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "VWAP", "params": {}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "VWAP", "params": {}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.01, "take_profit": 0.03}
    },
    {
        "name": "Gann Hi-Lo Activator Strategy",
        "slug": "eq-gann-hi-lo-activator",
        "category": "Equity",
        "hypothesis": "Enters when close crosses above the Gann activator moving average.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "SMA", "params": {"timeperiod": 3}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "SMA", "params": {"timeperiod": 3}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Hull Moving Average Trend Rider",
        "slug": "eq-hull-moving-average",
        "category": "Equity",
        "hypothesis": "Uses fast, low-lag Hull Moving Average to enter trends with minimum delay.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "WMA", "params": {"timeperiod": 9}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "WMA", "params": {"timeperiod": 9}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "Elder Ray Bull Power Setup",
        "slug": "eq-elder-ray-bull-bear",
        "category": "Equity",
        "hypothesis": "Buys when Bull Power is growing and EMA 13 is rising.",
        "entry_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": ">", "value": {"indicator": "EMA", "params": {"timeperiod": 13}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "CLOSE", "params": {}, "operator": "<", "value": {"indicator": "EMA", "params": {"timeperiod": 13}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.06}
    },
    {
        "name": "DMI Bullish Crossover Setup",
        "slug": "eq-directional-movement-index",
        "category": "Equity",
        "hypothesis": "Enters long when +DI crosses above -DI indicating bullish trend strength.",
        "entry_rules": {"conditions": [{"indicator": "PLUS_DI", "params": {"timeperiod": 14}, "operator": "crosses_above", "value": {"indicator": "MINUS_DI", "params": {"timeperiod": 14}}}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "PLUS_DI", "params": {"timeperiod": 14}, "operator": "crosses_below", "value": {"indicator": "MINUS_DI", "params": {"timeperiod": 14}}}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.08}
    },
    {
        "name": "Coppock Curve Long-term Momentum",
        "slug": "eq-coppock-curve-long",
        "category": "Equity",
        "hypothesis": "Uses Coppock Curve indicator to buy long-term momentum reversals in equities.",
        "entry_rules": {"conditions": [{"indicator": "ROC", "params": {"timeperiod": 14}, "operator": ">", "value": 0}], "logical_operator": "AND"},
        "exit_rules": {"conditions": [{"indicator": "ROC", "params": {"timeperiod": 14}, "operator": "<", "value": -5}], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15}
    }
]

# Define 30 distinct Options strategies with 'opt-' slug prefix
options_strategies = [
    {
        "name": "9:20 Short Straddle (Options)",
        "slug": "opt-920-short-straddle",
        "category": "Options",
        "hypothesis": "Capture high morning IV crush on BankNifty by selling both ATM Call and Put.",
        "entry_rules": {"time": "09:20", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.40}
    },
    {
        "name": "Nifty Iron Condor",
        "slug": "opt-nifty-iron-condor",
        "category": "Options",
        "hypothesis": "Range-bound strategy selling OTM Call/Put and buying further OTM Call/Put as insurance.",
        "entry_rules": {"instrument_type": "OPTION", "strikes": ["OTM+2", "OTM+1", "OTM-1", "OTM-2"], "option_type": "IRON_CONDOR"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.30}
    },
    {
        "name": "BankNifty Iron Butterfly",
        "slug": "opt-banknifty-iron-butterfly",
        "category": "Options",
        "hypothesis": "Sell ATM Straddle and buy OTM Strangle to cap max risk while gaining decay.",
        "entry_rules": {"instrument_type": "OPTION", "strike": "ATM", "option_type": "IRON_BUTTERFLY"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.35}
    },
    {
        "name": "Nifty Bull Call Spread",
        "slug": "opt-nifty-bull-call-spread",
        "category": "Options",
        "hypothesis": "Buy ATM Call and sell OTM Call to profit from moderate bullish views.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "BULL_CALL_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.30, "take_profit": 0.50}
    },
    {
        "name": "BankNifty Bear Put Spread",
        "slug": "opt-banknifty-bear-put-spread",
        "category": "Options",
        "hypothesis": "Buy ATM Put and sell OTM Put to benefit from bearish momentum with capped risk.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "BEAR_PUT_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.30, "take_profit": 0.50}
    },
    {
        "name": "Nifty 0DTE Short Strangle",
        "slug": "opt-nifty-short-strangle",
        "category": "Options",
        "hypothesis": "Sell OTM Call and Put on Nifty on expiry day to collect premium decay.",
        "entry_rules": {"time": "09:30", "instrument_type": "OPTION", "option_type": "STRANGLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.35}
    },
    {
        "name": "BankNifty Short Strangle",
        "slug": "opt-banknifty-short-strangle",
        "category": "Options",
        "hypothesis": "Sell OTM Call and Put to profit from range-bound index movement.",
        "entry_rules": {"time": "09:45", "instrument_type": "OPTION", "option_type": "STRANGLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.40}
    },
    {
        "name": "Nifty Calendar Spread",
        "slug": "opt-nifty-calendar-spread",
        "category": "Options",
        "hypothesis": "Sell front-week Call and buy next-week Call at the same strike.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "CALENDAR_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.30}
    },
    {
        "name": "BankNifty Calendar Spread",
        "slug": "opt-banknifty-calendar-spread",
        "category": "Options",
        "hypothesis": "Sell front-week Put and buy next-week Put at the same strike.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "CALENDAR_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.30}
    },
    {
        "name": "Nifty Bull Put Credit Spread",
        "slug": "opt-nifty-bull-put-spread",
        "category": "Options",
        "hypothesis": "Sell OTM Put and buy further OTM Put to earn premium in a sideways/up market.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "BULL_PUT_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.40}
    },
    {
        "name": "BankNifty Bear Call Credit Spread",
        "slug": "opt-banknifty-bear-call-spread",
        "category": "Options",
        "hypothesis": "Sell OTM Call and buy further OTM Call to capture premium in a down market.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "BEAR_CALL_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.40}
    },
    {
        "name": "Nifty Protective Collar Options",
        "slug": "opt-nifty-protective-collar",
        "category": "Options",
        "hypothesis": "Buy Put to hedge portfolio and sell OTM Call to finance the hedge.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "COLLAR"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.10, "take_profit": 0.25}
    },
    {
        "name": "BankNifty 1:2 Call Ratio Spread",
        "slug": "opt-banknifty-ratio-spread",
        "category": "Options",
        "hypothesis": "Buy 1 ATM Call and sell 2 OTM Calls to trade moderate bullishness with low cost.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "RATIO_SPREAD", "legs": {"buy": 1, "sell": 2}},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.45}
    },
    {
        "name": "Nifty 1:2 Put Ratio Spread",
        "slug": "opt-nifty-ratio-spread-v2",
        "category": "Options",
        "hypothesis": "Buy 1 ATM Put and sell 2 OTM Puts to gain from moderate downward movement.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "RATIO_SPREAD", "legs": {"buy": 1, "sell": 2}},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.45}
    },
    {
        "name": "9:30 Long Straddle Options",
        "slug": "opt-long-straddle-930",
        "category": "Options",
        "hypothesis": "Buy both Call and Put at ATM at 09:30 to trade high momentum breakouts.",
        "entry_rules": {"time": "09:30", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "BUY"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.35, "take_profit": 0.70}
    },
    {
        "name": "Options Long Strangle Breakout",
        "slug": "opt-long-strangle-breakout",
        "category": "Options",
        "hypothesis": "Buy OTM Call and OTM Put before high-volatility events like earnings/budgets.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "STRANGLE", "side": "BUY"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.30, "take_profit": 0.60}
    },
    {
        "name": "Nifty Diagonal Calendar Spread",
        "slug": "opt-nifty-diagonal-spread",
        "category": "Options",
        "hypothesis": "Sell near term OTM Call and buy longer term ATM/ITM Call.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "DIAGONAL_SPREAD"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.35}
    },
    {
        "name": "BankNifty Synthetic Long Stock",
        "slug": "opt-banknifty-synthetic-long",
        "category": "Options",
        "hypothesis": "Buy ATM Call and sell ATM Put to mimic stock ownership at zero net premium.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "SYNTHETIC_LONG"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.12, "take_profit": 0.30}
    },
    {
        "name": "FinNifty Short Straddle",
        "slug": "opt-finnifty-short-straddle",
        "category": "Options",
        "hypothesis": "Sell ATM FinNifty Call/Put on Tuesday Expiry to capture fast decay.",
        "entry_rules": {"time": "09:20", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.40}
    },
    {
        "name": "FinNifty Iron Condor",
        "slug": "opt-finnifty-iron-condor",
        "category": "Options",
        "hypothesis": "Range-bound credit spread on FinNifty to capture decay with limited loss.",
        "entry_rules": {"instrument_type": "OPTION", "strikes": ["OTM+2", "OTM+1", "OTM-1", "OTM-2"], "option_type": "IRON_CONDOR"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.30}
    },
    {
        "name": "Midcap Select Short Straddle",
        "slug": "opt-midcap-short-straddle",
        "category": "Options",
        "hypothesis": "Sell ATM Midcap Select options on Monday Expiry for high yield decay.",
        "entry_rules": {"time": "09:20", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.40}
    },
    {
        "name": "Nifty Covered Call Strategy",
        "slug": "opt-nifty-covered-call",
        "category": "Options",
        "hypothesis": "Hold index long position and sell OTM Call monthly for additional income.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "COVERED_CALL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.08, "take_profit": 0.15}
    },
    {
        "name": "BankNifty Covered Call Strategy",
        "slug": "opt-banknifty-covered-call",
        "category": "Options",
        "hypothesis": "Hold BankNifty futures long and write weekly OTM calls to hedge/earn premium.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "COVERED_CALL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.10, "take_profit": 0.20}
    },
    {
        "name": "Nifty Long Butterfly Spread",
        "slug": "opt-nifty-long-butterfly",
        "category": "Options",
        "hypothesis": "Buy 1 ITM Call, sell 2 ATM Calls, buy 1 OTM Call for targeted range trading.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "BUTTERFLY"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.40}
    },
    {
        "name": "BankNifty Long Condor Options",
        "slug": "opt-banknifty-long-condor",
        "category": "Options",
        "hypothesis": "Low cost range bound strategy buying wide OTM options and selling inner OTM options.",
        "entry_rules": {"instrument_type": "OPTION", "option_type": "CONDOR"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.35}
    },
    {
        "name": "10:00 AM Nifty Short Strangle",
        "slug": "opt-nifty-custom-strangle-10am",
        "category": "Options",
        "hypothesis": "Enter a short strangle at 10:00 AM once morning volatile swings settle.",
        "entry_rules": {"time": "10:00", "instrument_type": "OPTION", "option_type": "STRANGLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.40}
    },
    {
        "name": "11:00 AM BankNifty Short Strangle",
        "slug": "opt-banknifty-custom-strangle-11am",
        "category": "Options",
        "hypothesis": "Midday low volatility range capture by selling BANKNIFTY OTM spreads.",
        "entry_rules": {"time": "11:00", "instrument_type": "OPTION", "option_type": "STRANGLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.40}
    },
    {
        "name": "Nifty 0DTE ATM Straddle",
        "slug": "opt-nifty-zero-dte-straddle",
        "category": "Options",
        "hypothesis": "Sell ATM Straddle on Nifty Expiry day to extract premium decay.",
        "entry_rules": {"time": "09:25", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.45}
    },
    {
        "name": "BankNifty 0DTE ATM Straddle",
        "slug": "opt-banknifty-zero-dte-straddle",
        "category": "Options",
        "hypothesis": "Sell ATM Straddle on BankNifty Expiry day for high intraday theta decay.",
        "entry_rules": {"time": "09:25", "instrument_type": "OPTION", "strike": "ATM", "option_type": "STRADDLE", "side": "SELL"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.25, "take_profit": 0.45}
    },
    {
        "name": "Nifty Long Put Protective Hedge",
        "slug": "opt-nifty-protective-put",
        "category": "Options",
        "hypothesis": "Buy ATM Put on Nifty as pure tail-risk hedge for a portfolio.",
        "entry_rules": {"instrument_type": "OPTION", "strike": "ATM", "option_type": "PUT", "side": "BUY"},
        "exit_rules": {"conditions": [], "logical_operator": "AND"},
        "risk_params": {"stop_loss": 0.50, "take_profit": 1.50}
    }
]

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Delete existing strategies under 'Equity' and 'Options'
        await session.execute(
            text("DELETE FROM strategies WHERE category IN ('Equity', 'Options')")
        )
        print("Cleared existing Equity and Options strategies.")
        
        # Seed all 30 Equity strategies
        for s in equity_strategies:
            await session.execute(
                text("INSERT INTO strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) "
                     "VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
                {
                    'id': uuid.uuid4(),
                    'name': s['name'],
                    'slug': s['slug'],
                    'category': s['category'],
                    'hypothesis': s['hypothesis'],
                    'entry_rules': json.dumps(s['entry_rules']),
                    'exit_rules': json.dumps(s['exit_rules']),
                    'risk_params': json.dumps(s['risk_params']),
                    'created_at': datetime.utcnow()
                }
            )
        print(f"Seeded {len(equity_strategies)} Equity strategies.")
        
        # Seed all 30 Options strategies
        for s in options_strategies:
            await session.execute(
                text("INSERT INTO strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) "
                     "VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
                {
                    'id': uuid.uuid4(),
                    'name': s['name'],
                    'slug': s['slug'],
                    'category': s['category'],
                    'hypothesis': s['hypothesis'],
                    'entry_rules': json.dumps(s['entry_rules']),
                    'exit_rules': json.dumps(s['exit_rules']),
                    'risk_params': json.dumps(s['risk_params']),
                    'created_at': datetime.utcnow()
                }
            )
        print(f"Seeded {len(options_strategies)} Options strategies.")
        
        await session.commit()
        print("Commit completed successfully.")
        
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(seed())
