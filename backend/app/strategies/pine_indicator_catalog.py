"""TradingView Pine Script indicator catalog — seeded into pine_indicators table."""

from __future__ import annotations

from ..backtest.indicator_db import INDICATORS_DB

# TA-Lib / backtest engine name → TradingView Pine v5 function
_PINE_FN_MAP: dict[str, str] = {
    "SMA": "ta.sma",
    "EMA": "ta.ema",
    "WMA": "ta.wma",
    "DEMA": "ta.dema",
    "TEMA": "ta.tema",
    "TRIMA": "ta.trima",
    "KAMA": "ta.kama",
    "T3": "ta.t3",
    "SAR": "ta.sar",
    "BBANDS": "ta.bb",
    "MIDPOINT": "ta.median",
    "MIDPRICE": "ta.median",
    "VWAP": "ta.vwap",
    "RSI": "ta.rsi",
    "MACD": "ta.macd",
    "CCI": "ta.cci",
    "ADX": "ta.adx",
    "ADXR": "ta.adx",
    "DX": "ta.dmi",
    "MFI": "ta.mfi",
    "MOM": "ta.mom",
    "ROC": "ta.roc",
    "ROCP": "ta.roc",
    "WILLR": "ta.wpr",
    "STOCH": "ta.stoch",
    "STOCHRSI": "ta.stoch",
    "APO": "ta.apo",
    "PPO": "ta.ppo",
    "ULTOSC": "ta.ultosc",
    "BOP": "ta.bop",
    "CMO": "ta.cmo",
    "AROON": "ta.aroon",
    "AROONOSC": "ta.aroon",
    "PLUS_DI": "ta.dmi",
    "MINUS_DI": "ta.dmi",
    "ATR": "ta.atr",
    "NATR": "ta.atr",
    "TRANGE": "ta.tr",
    "OBV": "ta.obv",
    "AD": "ta.accdist",
    "ADOSC": "ta.accdist",
    "AVGPRICE": "ohlc4",
    "MEDPRICE": "hl2",
    "TYPPRICE": "hlc3",
    "WCLPRICE": "hlc3",
    "BETA": "ta.correlation",
    "CORREL": "ta.correlation",
    "STDDEV": "ta.stdev",
    "LINEARREG": "ta.linreg",
    "TSF": "ta.linreg",
    "CLOSE": "close",
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "VOLUME": "volume",
}

# TradingView Pine built-ins not in TA-Lib backtest DB
_TRADINGVIEW_EXTRAS: list[dict] = [
    {
        "name": "CROSSOVER",
        "pine_name": "ta.crossover",
        "long_name": "Crossover",
        "category": "Utility",
        "params": {},
        "inputs": ["series_a", "series_b"],
        "description": "True when series_a crosses above series_b.",
        "backtest_supported": False,
    },
    {
        "name": "CROSSUNDER",
        "pine_name": "ta.crossunder",
        "long_name": "Crossunder",
        "category": "Utility",
        "params": {},
        "inputs": ["series_a", "series_b"],
        "description": "True when series_a crosses below series_b.",
        "backtest_supported": False,
    },
    {
        "name": "HIGHEST",
        "pine_name": "ta.highest",
        "long_name": "Highest",
        "category": "Utility",
        "params": {"length": 14},
        "inputs": ["source"],
        "description": "Highest value over N bars.",
        "backtest_supported": False,
    },
    {
        "name": "LOWEST",
        "pine_name": "ta.lowest",
        "long_name": "Lowest",
        "category": "Utility",
        "params": {"length": 14},
        "inputs": ["source"],
        "description": "Lowest value over N bars.",
        "backtest_supported": False,
    },
    {
        "name": "HMA",
        "pine_name": "ta.hma",
        "long_name": "Hull Moving Average",
        "category": "Overlap Studies",
        "params": {"length": 14},
        "inputs": ["close"],
        "description": "Hull MA — low-lag smooth moving average.",
        "backtest_supported": False,
    },
    {
        "name": "ALMA",
        "pine_name": "ta.alma",
        "long_name": "Arnaud Legoux Moving Average",
        "category": "Overlap Studies",
        "params": {"length": 9, "offset": 0.85, "sigma": 6},
        "inputs": ["close"],
        "description": "Gaussian-distribution weighted moving average.",
        "backtest_supported": False,
    },
    {
        "name": "SWMA",
        "pine_name": "ta.swma",
        "long_name": "Symmetrically Weighted MA",
        "category": "Overlap Studies",
        "params": {"length": 14},
        "inputs": ["close"],
        "description": "Symmetrically weighted moving average.",
        "backtest_supported": False,
    },
    {
        "name": "VWMA",
        "pine_name": "ta.vwma",
        "long_name": "Volume Weighted MA",
        "category": "Overlap Studies",
        "params": {"length": 20},
        "inputs": ["close", "volume"],
        "description": "Moving average weighted by volume.",
        "backtest_supported": False,
    },
    {
        "name": "RMA",
        "pine_name": "ta.rma",
        "long_name": "Running Moving Average",
        "category": "Overlap Studies",
        "params": {"length": 14},
        "inputs": ["close"],
        "description": "Wilder's smoothing / RMA used in RSI and ATR.",
        "backtest_supported": False,
    },
    {
        "name": "SUPERTREND",
        "pine_name": "ta.supertrend",
        "long_name": "Supertrend",
        "category": "Trend",
        "params": {"factor": 3, "atr_period": 10},
        "inputs": ["high", "low", "close"],
        "description": "ATR-based trend-following overlay indicator.",
        "backtest_supported": False,
    },
    {
        "name": "KC",
        "pine_name": "ta.kc",
        "long_name": "Keltner Channels",
        "category": "Volatility",
        "params": {"length": 20, "mult": 1.5},
        "inputs": ["close"],
        "description": "EMA-centered volatility envelope channels.",
        "backtest_supported": False,
    },
    {
        "name": "DONCHIAN",
        "pine_name": "ta.donchian",
        "long_name": "Donchian Channels",
        "category": "Volatility",
        "params": {"length": 20},
        "inputs": ["high", "low"],
        "description": "Highest high / lowest low channel breakout system.",
        "backtest_supported": False,
    },
    {
        "name": "PIVOT_HIGH",
        "pine_name": "ta.pivothigh",
        "long_name": "Pivot High",
        "category": "Utility",
        "params": {"left_bars": 5, "right_bars": 5},
        "inputs": ["high"],
        "description": "Detects swing pivot highs.",
        "backtest_supported": False,
    },
    {
        "name": "PIVOT_LOW",
        "pine_name": "ta.pivotlow",
        "long_name": "Pivot Low",
        "category": "Utility",
        "params": {"left_bars": 5, "right_bars": 5},
        "inputs": ["low"],
        "description": "Detects swing pivot lows.",
        "backtest_supported": False,
    },
    {
        "name": "PERCENTRANK",
        "pine_name": "ta.percentrank",
        "long_name": "Percent Rank",
        "category": "Utility",
        "params": {"length": 20},
        "inputs": ["source"],
        "description": "Percentile rank of current value within lookback window.",
        "backtest_supported": False,
    },
    {
        "name": "CHANGE",
        "pine_name": "ta.change",
        "long_name": "Change",
        "category": "Utility",
        "params": {"length": 1},
        "inputs": ["source"],
        "description": "Difference between current and N bars ago.",
        "backtest_supported": False,
    },
    {
        "name": "HL2",
        "pine_name": "hl2",
        "long_name": "HL2",
        "category": "Price",
        "params": {},
        "inputs": ["high", "low"],
        "description": "(high + low) / 2",
        "backtest_supported": False,
    },
    {
        "name": "HLC3",
        "pine_name": "hlc3",
        "long_name": "HLC3",
        "category": "Price",
        "params": {},
        "inputs": ["high", "low", "close"],
        "description": "(high + low + close) / 3",
        "backtest_supported": False,
    },
    {
        "name": "OHLC4",
        "pine_name": "ohlc4",
        "long_name": "OHLC4",
        "category": "Price",
        "params": {},
        "inputs": ["open", "high", "low", "close"],
        "description": "(open + high + low + close) / 4",
        "backtest_supported": False,
    },
    {
        "name": "VI",
        "pine_name": "ta.vi",
        "long_name": "Vortex Indicator",
        "category": "Momentum",
        "params": {"length": 14},
        "inputs": ["high", "low", "close"],
        "description": "Identifies start of new trends via vortex lines.",
        "backtest_supported": False,
    },
    {
        "name": "ACCBANDS",
        "pine_name": "ta.accbands",
        "long_name": "Acceleration Bands",
        "category": "Volatility",
        "params": {"length": 20, "factor": 0.001},
        "inputs": ["high", "low", "close"],
        "description": "Volatility envelope for breakout detection.",
        "backtest_supported": False,
    },
    {
        "name": "COG",
        "pine_name": "ta.cog",
        "long_name": "Center of Gravity",
        "category": "Momentum",
        "params": {"length": 10},
        "inputs": ["close"],
        "description": "Ehlers Center of Gravity oscillator.",
        "backtest_supported": False,
    },
    {
        "name": "DEV",
        "pine_name": "ta.dev",
        "long_name": "Deviation",
        "category": "Statistics",
        "params": {"length": 20},
        "inputs": ["source"],
        "description": "Standard deviation from mean over N bars.",
        "backtest_supported": False,
    },
    {
        "name": "RANGE",
        "pine_name": "ta.range",
        "long_name": "Range",
        "category": "Utility",
        "params": {"length": 14},
        "inputs": ["source"],
        "description": "Max minus min over N bars.",
        "backtest_supported": False,
    },
    {
        "name": "WPR",
        "pine_name": "ta.wpr",
        "long_name": "Williams %R",
        "category": "Momentum",
        "params": {"length": 14},
        "inputs": ["high", "low", "close"],
        "description": "Williams Percent Range momentum oscillator.",
        "backtest_supported": False,
    },
    {
        "name": "DMI",
        "pine_name": "ta.dmi",
        "long_name": "Directional Movement Index",
        "category": "Momentum",
        "params": {"length": 14},
        "inputs": ["high", "low", "close"],
        "description": "Returns +DI, -DI, and ADX components.",
        "backtest_supported": False,
    },
    {
        "name": "ICHIMOKU",
        "pine_name": "ta.ichimoku",
        "long_name": "Ichimoku Cloud",
        "category": "Trend",
        "params": {"conversion_periods": 9, "base_periods": 26, "lagging_span2_periods": 52},
        "inputs": ["high", "low", "close"],
        "description": "Ichimoku Kinko Hyo trend system with cloud.",
        "backtest_supported": False,
    },
    {
        "name": "STRATEGY_ENTRY",
        "pine_name": "strategy.entry",
        "long_name": "Strategy Entry",
        "category": "Strategy",
        "params": {},
        "inputs": [],
        "description": "Places entry order in strategy() scripts.",
        "backtest_supported": False,
    },
    {
        "name": "STRATEGY_EXIT",
        "pine_name": "strategy.exit",
        "long_name": "Strategy Exit",
        "category": "Strategy",
        "params": {},
        "inputs": [],
        "description": "Places exit order with optional stop/limit in strategy().",
        "backtest_supported": False,
    },
    {
        "name": "STRATEGY_CLOSE",
        "pine_name": "strategy.close",
        "long_name": "Strategy Close",
        "category": "Strategy",
        "params": {},
        "inputs": [],
        "description": "Closes open position in strategy().",
        "backtest_supported": False,
    },
]

# Pine candlestick pattern names (TradingView ta.* pattern functions)
_TV_CANDLE_PATTERNS: list[tuple[str, str]] = [
    ("CDLHAMMER", "Hammer"),
    ("CDLENGULFING", "Engulfing"),
    ("CDLDOJI", "Doji"),
    ("CDLHARAMI", "Harami"),
    ("CDLMORNINGSTAR", "Morning Star"),
    ("CDLEVENINGSTAR", "Evening Star"),
    ("CDLSHOOTINGSTAR", "Shooting Star"),
    ("CDLMARUBOZU", "Marubozu"),
    ("CDLHANGINGMAN", "Hanging Man"),
    ("CDLINVERTEDHAMMER", "Inverted Hammer"),
    ("CDLPIERCING", "Piercing"),
    ("CDLDARKCLOUDCOVER", "Dark Cloud Cover"),
    ("CDL3WHITESOLDIERS", "Three White Soldiers"),
    ("CDL3BLACKCROWS", "Three Black Crows"),
    ("CDLMORNINGDOJISTAR", "Morning Doji Star"),
    ("CDLEVENINGDOJISTAR", "Evening Doji Star"),
    ("CDLDRAGONFLYDOJI", "Dragonfly Doji"),
    ("CDLGRAVESTONEDOJI", "Gravestone Doji"),
    ("CDLSPINNINGTOP", "Spinning Top"),
    ("CDLTASUKIGAP", "Tasuki Gap"),
]


def _from_indicator_db() -> list[dict]:
    rows: list[dict] = []
    for key, meta in INDICATORS_DB.items():
        pine_fn = _PINE_FN_MAP.get(key, f"// {key} — use equivalent Pine or custom logic")
        cat = meta.get("category", "Other")
        is_pattern = cat == "Pattern Recognition" or key.startswith("CDL")
        rows.append({
            "name": key,
            "pine_name": pine_fn if not is_pattern else f"// pattern:{key}",
            "long_name": meta.get("long_name", key),
            "category": cat,
            "description": meta.get("description", ""),
            "params": meta.get("params") or {},
            "inputs": meta.get("inputs") or [],
            "backtest_supported": True,
            "source": "talib",
        })
    return rows


def _pattern_extras() -> list[dict]:
    rows: list[dict] = []
    for code, label in _TV_CANDLE_PATTERNS:
        if code in INDICATORS_DB:
            continue
        rows.append({
            "name": code,
            "pine_name": f"// pattern:{code}",
            "long_name": label,
            "category": "Pattern Recognition",
            "description": f"TradingView candlestick pattern: {label}.",
            "params": {},
            "inputs": ["open", "high", "low", "close"],
            "backtest_supported": True,
            "source": "tradingview",
        })
    return rows


def build_indicator_catalog() -> list[dict]:
    """Full catalog: TA-Lib backtest indicators + TradingView Pine built-ins."""
    seen: set[str] = set()
    catalog: list[dict] = []

    for row in _from_indicator_db() + _pattern_extras() + _TRADINGVIEW_EXTRAS:
        name = row["name"]
        if name in seen:
            continue
        seen.add(name)
        catalog.append(row)

    return catalog


def format_catalog_for_llm(
    indicators: list[dict] | None = None,
    *,
    max_items: int = 120,
    backtest_only: bool = False,
) -> str:
    """Compact text block for LLM system/user prompts."""
    rows = indicators or build_indicator_catalog()
    if backtest_only:
        rows = [r for r in rows if r.get("backtest_supported")]

    lines = [
        "Available TradingView Pine / backtest indicators (use pine_name in Pine Script, name in strategy_spec):",
    ]
    by_cat: dict[str, list[dict]] = {}
    for r in rows[:max_items]:
        by_cat.setdefault(r.get("category", "Other"), []).append(r)

    for cat in sorted(by_cat.keys()):
        lines.append(f"\n[{cat}]")
        for r in by_cat[cat]:
            params = r.get("params") or {}
            param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else ""
            bt = "✓backtest" if r.get("backtest_supported") else "pine-only"
            desc = (r.get("description") or "")[:80]
            lines.append(
                f"  {r['name']}: {r['pine_name']}"
                + (f"({param_str})" if param_str else "")
                + f" [{bt}] — {desc}"
            )

    if len(rows) > max_items:
        lines.append(f"\n… and {len(rows) - max_items} more indicators in database.")

    return "\n".join(lines)
