INDICATORS_DB = {
    # OVERLAP STUDIES
    "SMA": {
        "name": "SMA",
        "long_name": "Simple Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "Calculates the average price of a security over a specified number of periods.",
        "inputs": ["close"]
    },
    "EMA": {
        "name": "EMA",
        "long_name": "Exponential Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "Calculates a moving average that places a greater weight and significance on the most recent data points.",
        "inputs": ["close"]
    },
    "WMA": {
        "name": "WMA",
        "long_name": "Weighted Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "A moving average that assigns linearly decreasing weights to older data points.",
        "inputs": ["close"]
    },
    "HMA": {
        "name": "HMA",
        "long_name": "Hull Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 14},
        "description": "A responsive moving average that reduces lag using weighted square-root periods.",
        "inputs": ["close"]
    },
    "VWMA": {
        "name": "VWMA",
        "long_name": "Volume Weighted Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 14},
        "description": "A moving average weighted by volume over each period.",
        "inputs": ["close", "volume"]
    },
    "DEMA": {
        "name": "DEMA",
        "long_name": "Double Exponential Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "A faster moving average that reduces lag by using double exponential calculation.",
        "inputs": ["close"]
    },
    "TEMA": {
        "name": "TEMA",
        "long_name": "Triple Exponential Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "Uses a triple exponential calculation to provide even less lag than DEMA.",
        "inputs": ["close"]
    },
    "TRIMA": {
        "name": "TRIMA",
        "long_name": "Triangular Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "A double-smoothed simple moving average that places the greatest weight in the middle of the period.",
        "inputs": ["close"]
    },
    "KAMA": {
        "name": "KAMA",
        "long_name": "Kaufman Adaptive Moving Average",
        "category": "Overlap Studies",
        "params": {"timeperiod": 30},
        "description": "An adaptive moving average that adjusts its speed based on market noise and volatility.",
        "inputs": ["close"]
    },
    "T3": {
        "name": "T3",
        "long_name": "Triple Exponential Moving Average (T3)",
        "category": "Overlap Studies",
        "params": {"timeperiod": 5, "vfactor": 0.7},
        "description": "A smooth moving average designed by Tim Tillson that reduces overshoot and lag.",
        "inputs": ["close"]
    },
    "SAR": {
        "name": "SAR",
        "long_name": "Parabolic SAR",
        "category": "Overlap Studies",
        "params": {"acceleration": 0.02, "maximum": 0.2},
        "description": "Draws dotted lines over the chart to determine trend direction and trailing stop-loss points.",
        "inputs": ["high", "low"]
    },
    "BBANDS": {
        "name": "BBANDS",
        "long_name": "Bollinger Bands",
        "category": "Overlap Studies",
        "params": {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2, "output_index": "middle"},
        "description": "A volatility band placed above and below a moving average, indicating relative high and low prices.",
        "inputs": ["close"]
    },
    "MIDPOINT": {
        "name": "MIDPOINT",
        "long_name": "Midpoint over Period",
        "category": "Overlap Studies",
        "params": {"timeperiod": 14},
        "description": "Calculates the average of the highest and lowest close prices over a period.",
        "inputs": ["close"]
    },
    "MIDPRICE": {
        "name": "MIDPRICE",
        "long_name": "Midpoint Price over Period",
        "category": "Overlap Studies",
        "params": {"timeperiod": 14},
        "description": "Calculates the average of the highest high and lowest low prices over a period.",
        "inputs": ["high", "low"]
    },
    "VWAP": {
        "name": "VWAP",
        "long_name": "Volume Weighted Average Price",
        "category": "Overlap Studies",
        "params": {},
        "description": "The average price a security has traded at throughout the day, based on both volume and price.",
        "inputs": ["close", "volume"]
    },

    # MOMENTUM INDICATORS
    "RSI": {
        "name": "RSI",
        "long_name": "Relative Strength Index",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures the speed and change of price movements, highlighting overbought (>70) or oversold (<30) states.",
        "inputs": ["close"]
    },
    "MACD": {
        "name": "MACD",
        "long_name": "Moving Average Convergence Divergence",
        "category": "Momentum Indicators",
        "params": {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "output_index": "macd"},
        "description": "A trend-following momentum indicator that shows the relationship between two moving averages of a security's price.",
        "inputs": ["close"]
    },
    "CCI": {
        "name": "CCI",
        "long_name": "Commodity Channel Index",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Assesses price trend strength and direction by comparing current price to historical average price.",
        "inputs": ["high", "low", "close"]
    },
    "ADX": {
        "name": "ADX",
        "long_name": "Average Directional Movement Index",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures the overall strength of a trend, regardless of its direction (values above 25 indicate a strong trend).",
        "inputs": ["high", "low", "close"]
    },
    "ADXR": {
        "name": "ADXR",
        "long_name": "Average Directional Movement Index Rating",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Evaluates the change in directional movement strength over a specified interval.",
        "inputs": ["high", "low", "close"]
    },
    "DX": {
        "name": "DX",
        "long_name": "Directional Movement Index",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures the directional movement without smoothing.",
        "inputs": ["high", "low", "close"]
    },
    "MFI": {
        "name": "MFI",
        "long_name": "Money Flow Index",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Uses both price and volume to measure buying and selling pressure. Similar to RSI but incorporates volume.",
        "inputs": ["high", "low", "close", "volume"]
    },
    "MOM": {
        "name": "MOM",
        "long_name": "Momentum",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 10},
        "description": "Measures the rate of change of a security's price by comparing the current price to the price N periods ago.",
        "inputs": ["close"]
    },
    "ROC": {
        "name": "ROC",
        "long_name": "Rate of Change",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 10},
        "description": "Measures the percentage change in price between the current price and the price N periods ago.",
        "inputs": ["close"]
    },
    "ROCP": {
        "name": "ROCP",
        "long_name": "Rate of Change Percentage",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 10},
        "description": "Calculates the rate of change percentage as a decimal fraction.",
        "inputs": ["close"]
    },
    "WILLR": {
        "name": "WILLR",
        "long_name": "Williams %R",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "A momentum indicator that measures overbought and oversold levels, oscillating between 0 and -100.",
        "inputs": ["high", "low", "close"]
    },
    "STOCH": {
        "name": "STOCH",
        "long_name": "Stochastic Oscillator",
        "category": "Momentum Indicators",
        "params": {"fastk_period": 5, "slowk_period": 3, "slowk_matype": 0, "slowd_period": 3, "slowd_matype": 0, "output_index": "slowk"},
        "description": "Compares a security's closing price to its price range over a given time period.",
        "inputs": ["high", "low", "close"]
    },
    "STOCHRSI": {
        "name": "STOCHRSI",
        "long_name": "Stochastic RSI",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14, "fastk_period": 5, "fastd_period": 3, "fastd_matype": 0, "output_index": "fastk"},
        "description": "Applies the Stochastic oscillator formula to Relative Strength Index values.",
        "inputs": ["close"]
    },
    "APO": {
        "name": "APO",
        "long_name": "Absolute Price Oscillator",
        "category": "Momentum Indicators",
        "params": {"fastperiod": 12, "slowperiod": 26, "matype": 0},
        "description": "Shows the difference between two moving averages in absolute terms.",
        "inputs": ["close"]
    },
    "PPO": {
        "name": "PPO",
        "long_name": "Percentage Price Oscillator",
        "category": "Momentum Indicators",
        "params": {"fastperiod": 12, "slowperiod": 26, "matype": 0},
        "description": "Shows the percentage difference between two moving averages.",
        "inputs": ["close"]
    },
    "ULTOSC": {
        "name": "ULTOSC",
        "long_name": "Ultimate Oscillator",
        "category": "Momentum Indicators",
        "params": {"timeperiod1": 7, "timeperiod2": 14, "timeperiod3": 28},
        "description": "Combines short, medium, and long-term price action into a single oscillator to reduce false breakouts.",
        "inputs": ["high", "low", "close"]
    },
    "BOP": {
        "name": "BOP",
        "long_name": "Balance Of Power",
        "category": "Momentum Indicators",
        "params": {},
        "description": "Measures the strength of buying and selling pressure, assessing price trend sustainability.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CMO": {
        "name": "CMO",
        "long_name": "Chande Momentum Oscillator",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Calculates momentum on both up and down days, oscillating between +100 and -100.",
        "inputs": ["close"]
    },
    "AROON": {
        "name": "AROON",
        "long_name": "Aroon",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14, "output_index": "down"},
        "description": "Indicates whether a security is trending and the strength of the trend.",
        "inputs": ["high", "low"]
    },
    "AROONOSC": {
        "name": "AROONOSC",
        "long_name": "Aroon Oscillator",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Oscillator derived by subtracting Aroon Down from Aroon Up.",
        "inputs": ["high", "low"]
    },
    "PLUS_DI": {
        "name": "PLUS_DI",
        "long_name": "+DI (Plus Directional Indicator)",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures the upward trend component of directional movement.",
        "inputs": ["high", "low", "close"]
    },
    "MINUS_DI": {
        "name": "MINUS_DI",
        "long_name": "-DI (Minus Directional Indicator)",
        "category": "Momentum Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures the downward trend component of directional movement.",
        "inputs": ["high", "low", "close"]
    },

    # VOLATILITY INDICATORS
    "ATR": {
        "name": "ATR",
        "long_name": "Average True Range",
        "category": "Volatility Indicators",
        "params": {"timeperiod": 14},
        "description": "Measures historical market volatility by averaging the true range of prices.",
        "inputs": ["high", "low", "close"]
    },
    "NATR": {
        "name": "NATR",
        "long_name": "Normalized Average True Range",
        "category": "Volatility Indicators",
        "params": {"timeperiod": 14},
        "description": "Normalized version of ATR expressed as a percentage of the closing price.",
        "inputs": ["high", "low", "close"]
    },
    "TRANGE": {
        "name": "TRANGE",
        "long_name": "True Range",
        "category": "Volatility Indicators",
        "params": {},
        "description": "Measures the absolute difference between high and low, or compared to the previous close.",
        "inputs": ["high", "low", "close"]
    },

    # VOLUME INDICATORS
    "OBV": {
        "name": "OBV",
        "long_name": "On Balance Volume",
        "category": "Volume Indicators",
        "params": {},
        "description": "Uses volume flow to predict changes in stock price, adding volume on up days and subtracting on down days.",
        "inputs": ["close", "volume"]
    },
    "AD": {
        "name": "AD",
        "long_name": "Chaikin Accumulation/Distribution Line",
        "category": "Volume Indicators",
        "params": {},
        "description": "Measures the cumulative flow of money into and out of a security based on price and volume.",
        "inputs": ["high", "low", "close", "volume"]
    },
    "ADOSC": {
        "name": "ADOSC",
        "long_name": "Chaikin Oscillator",
        "category": "Volume Indicators",
        "params": {"fastperiod": 3, "slowperiod": 10},
        "description": "Applies MACD formula to the Accumulation/Distribution line to identify money flow momentum.",
        "inputs": ["high", "low", "close", "volume"]
    },

    # PRICE TRANSFORM
    "AVGPRICE": {
        "name": "AVGPRICE",
        "long_name": "Average Price",
        "category": "Price Transform",
        "params": {},
        "description": "Calculates the average of open, high, low, and close prices.",
        "inputs": ["open", "high", "low", "close"]
    },
    "MEDPRICE": {
        "name": "MEDPRICE",
        "long_name": "Median Price",
        "category": "Price Transform",
        "params": {},
        "description": "Calculates the median of high and low prices.",
        "inputs": ["high", "low"]
    },
    "TYPPRICE": {
        "name": "TYPPRICE",
        "long_name": "Typical Price",
        "category": "Price Transform",
        "params": {},
        "description": "Calculates the average of high, low, and close prices.",
        "inputs": ["high", "low", "close"]
    },
    "WCLPRICE": {
        "name": "WCLPRICE",
        "long_name": "Weighted Close Price",
        "category": "Price Transform",
        "params": {},
        "description": "Calculates the weighted average of high, low, and double close prices.",
        "inputs": ["high", "low", "close"]
    },

    # STATISTIC FUNCTIONS
    "BETA": {
        "name": "BETA",
        "long_name": "Beta Coefficient",
        "category": "Statistic Functions",
        "params": {"timeperiod": 5},
        "description": "Measures the volatility of a security relative to a market benchmark.",
        "inputs": ["high", "low"]
    },
    "CORREL": {
        "name": "CORREL",
        "long_name": "Pearson's Correlation Coefficient",
        "category": "Statistic Functions",
        "params": {"timeperiod": 30},
        "description": "Calculates the correlation between two price streams over time.",
        "inputs": ["high", "low"]
    },
    "STDDEV": {
        "name": "STDDEV",
        "long_name": "Standard Deviation",
        "category": "Statistic Functions",
        "params": {"timeperiod": 5, "nbdev": 1},
        "description": "Measures the statistical dispersion of prices around their moving average.",
        "inputs": ["close"]
    },
    "LINEARREG": {
        "name": "LINEARREG",
        "long_name": "Linear Regression Forecast",
        "category": "Statistic Functions",
        "params": {"timeperiod": 14},
        "description": "Forecasts future price based on a linear regression model over a lookback window.",
        "inputs": ["close"]
    },
    "TSF": {
        "name": "TSF",
        "long_name": "Time Series Forecast",
        "category": "Statistic Functions",
        "params": {"timeperiod": 14},
        "description": "Calculates a time series regression line to forecast values.",
        "inputs": ["close"]
    },

    # PATTERN RECOGNITION (CDL PATTERNS)
    "CDL2CROWS": {
        "name": "CDL2CROWS",
        "long_name": "Two Crows Pattern",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bearish candlestick pattern occurring in uptrends (100 = bullish, -100 = bearish).",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDL3BLACKCROWS": {
        "name": "CDL3BLACKCROWS",
        "long_name": "Three Black Crows",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Strong bearish reversal pattern consisting of three consecutive long red candles.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDL3INSIDE": {
        "name": "CDL3INSIDE",
        "long_name": "Three Inside Up/Down",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Reversal pattern consisting of a Harami followed by a confirmation candle.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDL3LINESTRIKE": {
        "name": "CDL3LINESTRIKE",
        "long_name": "Three Line Strike",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Rare trend-continuation pattern consisting of three small candles and one large outer candle.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDL3OUTSIDE": {
        "name": "CDL3OUTSIDE",
        "long_name": "Three Outside Up/Down",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Reversal pattern consisting of an Engulfing pattern followed by a confirmation candle.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLHAMMER": {
        "name": "CDLHAMMER",
        "long_name": "Hammer",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bullish reversal pattern with a small body and a long lower shadow, occurring in downtrends.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLENGULFING": {
        "name": "CDLENGULFING",
        "long_name": "Engulfing Pattern",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Major reversal pattern where a large candle body fully overlaps/engulfs the previous day's body.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLDOJI": {
        "name": "CDLDOJI",
        "long_name": "Doji",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Indicates market indecision, where the open and close prices are virtually identical.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLHARAMI": {
        "name": "CDLHARAMI",
        "long_name": "Harami Pattern",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Two-day pattern where a small candle is fully contained within the large body of the previous day.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLMORNINGSTAR": {
        "name": "CDLMORNINGSTAR",
        "long_name": "Morning Star",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bullish three-day reversal pattern signaling transition from a downtrend to an uptrend.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLEVENINGSTAR": {
        "name": "CDLEVENINGSTAR",
        "long_name": "Evening Star",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bearish three-day reversal pattern signaling transition from an uptrend to a downtrend.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLSHOOTINGSTAR": {
        "name": "CDLSHOOTINGSTAR",
        "long_name": "Shooting Star",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bearish reversal pattern with a long upper shadow and a small body near the daily low.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLMARUBOZU": {
        "name": "CDLMARUBOZU",
        "long_name": "Marubozu",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Candle with no shadows (or extremely short ones), indicating strong buy or sell pressure.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLHANGINGMAN": {
        "name": "CDLHANGINGMAN",
        "long_name": "Hanging Man",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bearish reversal pattern that looks like a Hammer but occurs at the top of an uptrend.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLINVERTEDHAMMER": {
        "name": "CDLINVERTEDHAMMER",
        "long_name": "Inverted Hammer",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bullish reversal pattern characterized by a long upper shadow and a small body near the low.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLPIERCING": {
        "name": "CDLPIERCING",
        "long_name": "Piercing Pattern",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Two-day bullish reversal pattern where a green candle closes above the midpoint of the prior red candle.",
        "inputs": ["open", "high", "low", "close"]
    },
    "CDLDARKCLOUDCOVER": {
        "name": "CDLDARKCLOUDCOVER",
        "long_name": "Dark Cloud Cover",
        "category": "Pattern Recognition",
        "params": {},
        "description": "Bearish two-day reversal pattern where a red candle opens above the prior close and closes below its midpoint.",
        "inputs": ["open", "high", "low", "close"]
    }
}

# Add remaining standard patterns dynamically to cross 100+ count
PATTERNS = [
    ("CDL3STARSINSOUTH", "Three Stars In The South"),
    ("CDL3WHITESOLDIERS", "Three Advancing White Soldiers"),
    ("CDLABANDONEDBABY", "Abandoned Baby"),
    ("CDLADVANCEBLOCK", "Advance Block"),
    ("CDLBELTHOLD", "Belt-hold"),
    ("CDLBREAKAWAY", "Breakaway"),
    ("CDLCLOSINGMARUBOZU", "Closing Marubozu"),
    ("CDLCONCEALBABYSWALL", "Concealing Baby Swallow"),
    ("CDLCOUNTERATTACK", "Counterattack"),
    ("CDLDRAGONFLYDOJI", "Dragonfly Doji"),
    ("CDLEVENINGDOJISTAR", "Evening Doji Star"),
    ("CDLGAPSIDESIDEWHITE", "Up/Down-gap Side-by-Side White Lines"),
    ("CDLGRAVESTONEDOJI", "Gravestone Doji"),
    ("CDLHARAMICROSS", "Harami Cross Pattern"),
    ("CDLHIGHWAVE", "High-Wave Candle"),
    ("CDLHIKKAKE", "Hikkake Pattern"),
    ("CDLHIKKAKEMOD", "Modified Hikkake Pattern"),
    ("CDLHOMINGPIGEON", "Homing Pigeon"),
    ("CDLIDENTICAL3CROWS", "Identical Three Crows"),
    ("CDLINNECK", "In-Neck Pattern"),
    ("CDLKICKING", "Kicking Pattern"),
    ("CDLKICKINGBYLENGTH", "Kicking - bull/bear determined by longer candle"),
    ("CDLLADDERBOTTOM", "Ladder Bottom"),
    ("CDLLONGLEGGEDDOJI", "Long Legged Doji"),
    ("CDLLONGLINE", "Long Line Candle"),
    ("CDLMATCHINGLOW", "Matching Low"),
    ("CDLMATHOLD", "Mat Hold"),
    ("CDLMORNINGDOJISTAR", "Morning Doji Star"),
    ("CDLONNECK", "On-Neck Pattern"),
    ("CDLRICKSWAW", "Rickshaw Man"),
    ("CDLRISEFALL3METHODS", "Rising/Falling Three Methods"),
    ("CDLSEPARATINGLINES", "Separating Lines"),
    ("CDLSHORTLINE", "Short Line Candle"),
    ("CDLSPINNINGTOP", "Spinning Top"),
    ("CDLSTALLEDPATTERN", "Stalled Pattern"),
    ("CDLSTICKSANDWICH", "Stick Sandwich"),
    ("CDLTAKURI", "Takuri (Dragonfly Doji with very long lower shadow)"),
    ("CDLTASUKIGAP", "Tasuki Gap"),
    ("CDLTHRUSTING", "Thrusting Pattern"),
    ("CDLTRISTAR", "Tristar Pattern"),
    ("CDLUNIQUE3RIVER", "Unique 3 River"),
    ("CDLUPSIDEGAP2CROWS", "Upside Gap Two Crows"),
    ("CDLXSIDEGAP3METHODS", "Upside/Downside Gap Three Methods")
]

for pat_code, pat_name in PATTERNS:
    if pat_code not in INDICATORS_DB:
        INDICATORS_DB[pat_code] = {
            "name": pat_code,
            "long_name": pat_name,
            "category": "Pattern Recognition",
            "params": {},
            "description": f"Candlestick pattern recognition function for {pat_name} (returns positive/negative values).",
            "inputs": ["open", "high", "low", "close"]
        }
