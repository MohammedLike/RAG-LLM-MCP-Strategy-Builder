TEMPLATES = {
    "sma_crossover": {
        "name": "SMA Crossover",
        "description": "Golden cross / death cross dual moving average crossover",
        "category": "Trend Following",
        "instrument_type": "EQUITY",
        "entry": {
            "conditions": [{"indicator": "SMA", "params": {"timeperiod": 20}, "operator": "crosses_above", "value": {"indicator": "SMA", "params": {"timeperiod": 50}}}],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [{"indicator": "SMA", "params": {"timeperiod": 20}, "operator": "crosses_below", "value": {"indicator": "SMA", "params": {"timeperiod": 50}}}],
            "logical_operator": "AND"
        }
    },
    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "description": "Buy oversold, sell overbought using RSI",
        "category": "Mean Reversion",
        "instrument_type": "EQUITY",
        "entry": {
            "conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "<", "value": 30}],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": ">", "value": 70}],
            "logical_operator": "AND"
        }
    },
    "bollinger_breakout": {
        "name": "Bollinger Band Breakout",
        "description": "Buy when price breaks above upper Bollinger Band",
        "category": "Volatility",
        "instrument_type": "EQUITY",
        "entry": {
            "conditions": [{"indicator": "CLOSE", "operator": "crosses_above", "value": {"indicator": "BBANDS", "params": {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2, "output_index": "upper"}}}],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [{"indicator": "CLOSE", "operator": "crosses_below", "value": {"indicator": "BBANDS", "params": {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2, "output_index": "middle"}}}],
            "logical_operator": "AND"
        }
    },
    "macd_momentum": {
        "name": "MACD Momentum",
        "description": "Buy when MACD crosses above signal line",
        "category": "Momentum",
        "instrument_type": "EQUITY",
        "entry": {
            "conditions": [{"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "macd"}, "operator": "crosses_above", "value": {"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "signal"}}}],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [{"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "macd"}, "operator": "crosses_below", "value": {"indicator": "MACD", "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "signal"}}}],
            "logical_operator": "AND"
        }
    },
    "short_strangle": {
        "name": "Short Strangle",
        "description": "Sell OTM CE + PE on BankNifty weekly expiry",
        "category": "Options Selling",
        "instrument_type": "OPTION",
        "strike": "OTM+1",
        "option_type": "STRADDLE",
        "entry": {"conditions": [], "logical_operator": "AND"},
        "exit": {"conditions": [], "logical_operator": "AND"},
        "stop_loss": 0.20,
        "take_profit": 0.50
    },
    "atm_straddle": {
        "name": "ATM Straddle",
        "description": "Buy ATM CE + PE for earnings/event play",
        "category": "Options Buying",
        "instrument_type": "OPTION",
        "strike": "ATM",
        "option_type": "STRADDLE",
        "is_credit": False,
        "entry": {"conditions": [], "logical_operator": "AND"},
        "exit": {"conditions": [], "logical_operator": "AND"},
        "stop_loss": 0.30,
        "take_profit": 0.50
    },
    "momentum_equity": {
        "name": "Momentum Equity",
        "description": "Buy when price > SMA 50 and RSI > 50",
        "category": "Momentum",
        "instrument_type": "EQUITY",
        "entry": {
            "conditions": [
                {"indicator": "CLOSE", "operator": ">", "value": {"indicator": "SMA", "params": {"timeperiod": 50}}},
                {"indicator": "RSI", "params": {"timeperiod": 14}, "operator": ">", "value": 50}
            ],
            "logical_operator": "AND"
        },
        "exit": {
            "conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "<", "value": 30}],
            "logical_operator": "AND"
        }
    }
}
