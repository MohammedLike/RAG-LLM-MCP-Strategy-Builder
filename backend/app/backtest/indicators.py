import pandas as pd
import numpy as np
from .indicator_db import INDICATORS_DB

class IndicatorManager:
    """Manages 100+ technical indicators for backtesting using pure numpy/pandas implementations."""

    _ALIASES = {
        "PLUSDI": "PLUS_DI",
        "MINUSDI": "MINUS_DI",
        "DMI_PLUS": "PLUS_DI",
        "DMI_MINUS": "MINUS_DI",
        "BB": "BBANDS",
        "BOLLINGER": "BBANDS",
        "BOLLINGER_BANDS": "BBANDS",
        "SIMPLE_MOVING_AVERAGE": "SMA",
        "EXPONENTIAL_MOVING_AVERAGE": "EMA",
        "WILLIAMS_R": "WILLR",
        "WILLIAMS_PERCENT_R": "WILLR",
    }

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized = name.upper().strip().replace(" ", "_").replace("-", "_")
        return IndicatorManager._ALIASES.get(normalized, normalized)

    @staticmethod
    def get_indicators_list():
        return INDICATORS_DB

    @staticmethod
    def apply_indicator(df: pd.DataFrame, name: str, params: dict = None) -> pd.Series:
        if params is None:
            params = {}
        name = IndicatorManager.normalize_name(name)

        if name == "VWAP":
            pv = df['close'] * df['volume']
            return pv.cumsum() / df['volume'].cumsum()

        if name in ["DELTA", "GAMMA", "THETA", "VEGA", "IV"]:
            col_name = name.lower()
            if col_name in df.columns:
                return df[col_name]
            return pd.Series(0.0, index=df.index)

        if name in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME"]:
            return df[name.lower()]

        func_map = {
            "SMA": IndicatorManager._sma,
            "EMA": IndicatorManager._ema,
            "RSI": IndicatorManager._rsi,
            "MACD": IndicatorManager._macd,
            "BBANDS": IndicatorManager._bbands,
            "ATR": IndicatorManager._atr,
            "ADX": IndicatorManager._adx,
            "CCI": IndicatorManager._cci,
            "STOCH": IndicatorManager._stoch,
            "WILLR": IndicatorManager._willr,
            "OBV": IndicatorManager._obv,
            "MOM": IndicatorManager._mom,
            "ROC": IndicatorManager._roc,
            "MFI": IndicatorManager._mfi,
            "WMA": IndicatorManager._wma,
            "KAMA": IndicatorManager._kama,
            "DEMA": IndicatorManager._dema,
            "TEMA": IndicatorManager._tema,
            "TRIMA": IndicatorManager._trima,
            "SAR": IndicatorManager._sar,
            "NATR": IndicatorManager._natr,
            "CMO": IndicatorManager._cmo,
            "APO": IndicatorManager._apo,
            "PPO": IndicatorManager._ppo,
            "AROON": IndicatorManager._aroon,
            "AROONOSC": IndicatorManager._aroonosc,
            "STDDEV": IndicatorManager._stddev,
            "LINEARREG": IndicatorManager._linearreg,
            "TSF": IndicatorManager._tsf,
            "VWAP": IndicatorManager._vwap,
            "MIDPOINT": IndicatorManager._midpoint,
            "MIDPRICE": IndicatorManager._midprice,
            "TYPPRICE": IndicatorManager._typprice,
            "AVGPRICE": IndicatorManager._avgprice,
            "MEDPRICE": IndicatorManager._medprice,
            "WCLPRICE": IndicatorManager._wclprice,
            "BOP": IndicatorManager._bop,
            "ULTOSC": IndicatorManager._ultosc,
            "DX": IndicatorManager._dx,
            "PLUS_DI": IndicatorManager._plus_di,
            "MINUS_DI": IndicatorManager._minus_di,
            "AD": IndicatorManager._ad,
            "ADOSC": IndicatorManager._adosc,
            "TRANGE": IndicatorManager._trange,
        }

        cdl_patterns = {k: v for k, v in INDICATORS_DB.items() if k.startswith("CDL")}
        for pat in cdl_patterns:
            func_map[pat] = lambda df, p=pat: IndicatorManager._cdl_pattern(df, p)

        if name in func_map:
            return func_map[name](df, params)

        if _has_talib:
            try:
                import talib
                func = getattr(talib, name, None)
                if func:
                    return IndicatorManager._apply_talib_func(df, func, name, params)
            except Exception:
                pass

        raise ValueError(f"Indicator {name} not available. Install TA-Lib or use one of: {', '.join(sorted(func_map.keys()))}")

    # ---- Core implementations ----
    @staticmethod
    def _sma(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        return df['close'].rolling(window=period).mean()

    @staticmethod
    def _ema(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        return df['close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def _wma(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        weights = np.arange(1, period + 1)
        return df['close'].rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    @staticmethod
    def _rsi(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        delta = df['close'].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _macd(df, params):
        fast = int(params.get('fastperiod', params.get('fast', 12)))
        slow = int(params.get('slowperiod', params.get('slow', 26)))
        signal = int(params.get('signalperiod', params.get('signal', 9)))
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        output_index = params.get('output_index', 'macd')
        if output_index == 'signal':
            return signal_line
        if output_index == 'hist':
            return hist
        return macd_line

    @staticmethod
    def _bbands(df, params):
        period = int(params.get('timeperiod', params.get('length', 20)))
        nbdev = float(params.get('nbdevup', params.get('std', 2)))
        middle = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = middle + nbdev * std
        lower = middle - nbdev * std
        output_index = params.get('output_index', 'middle')
        if output_index == 'upper':
            return upper
        if output_index == 'lower':
            return lower
        return middle

    @staticmethod
    def _atr(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    @staticmethod
    def _adx(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        high, low, close = df['high'], df['low'], df['close']
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = minus_dm.abs()
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        di_plus = 100 * (plus_dm.rolling(period).mean() / atr.replace(0, np.nan))
        di_minus = 100 * (minus_dm.rolling(period).mean() / atr.replace(0, np.nan))
        dx = 100 * ((di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan))
        return dx.rolling(period).mean()

    @staticmethod
    def _cci(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        return (tp - sma) / (0.015 * mad.replace(0, np.nan))

    @staticmethod
    def _stoch(df, params):
        k_period = int(params.get('fastk_period', params.get('k', 14)))
        d_period = int(params.get('slowd_period', params.get('d', 3)))
        low_min = df['low'].rolling(k_period).min()
        high_max = df['high'].rolling(k_period).max()
        slowk = 100 * ((df['close'] - low_min) / (high_max - low_min).replace(0, np.nan))
        slowd = slowk.rolling(d_period).mean()
        output_index = params.get('output_index', 'slowk')
        return slowd if output_index == 'slowd' else slowk

    @staticmethod
    def _willr(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        low_min = df['low'].rolling(period).min()
        high_max = df['high'].rolling(period).max()
        return -100 * ((high_max - df['close']) / (high_max - low_min).replace(0, np.nan))

    @staticmethod
    def _obv(df, params):
        obv = (df['volume'] * ((df['close'].diff() > 0).astype(int) * 2 - 1)).cumsum()
        return obv

    @staticmethod
    def _mom(df, params):
        period = int(params.get('timeperiod', params.get('length', 10)))
        return df['close'].diff(period)

    @staticmethod
    def _roc(df, params):
        period = int(params.get('timeperiod', params.get('length', 10)))
        return ((df['close'] - df['close'].shift(period)) / df['close'].shift(period).replace(0, np.nan)) * 100

    @staticmethod
    def _mfi(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        tp = (df['high'] + df['low'] + df['close']) / 3
        mf = tp * df['volume']
        positive_flow = mf.where(tp > tp.shift(), 0).rolling(period).sum()
        negative_flow = mf.where(tp < tp.shift(), 0).rolling(period).sum()
        mfr = positive_flow / negative_flow.replace(0, np.nan)
        return 100 - (100 / (1 + mfr))

    @staticmethod
    def _sar(df, params):
        acceleration = float(params.get('acceleration', 0.02))
        maximum = float(params.get('maximum', 0.2))
        high, low = df['high'], df['low']
        sar = low.copy()
        trend = 1
        af = acceleration
        extreme = high.iloc[0]
        for i in range(1, len(df)):
            if trend == 1:
                sar.iloc[i] = sar.iloc[i-1] + af * (extreme - sar.iloc[i-1])
                if low.iloc[i] < sar.iloc[i]:
                    trend = -1
                    sar.iloc[i] = extreme
                    extreme = low.iloc[i]
                    af = acceleration
                else:
                    if high.iloc[i] > extreme:
                        extreme = high.iloc[i]
                        af = min(af + acceleration, maximum)
            else:
                sar.iloc[i] = sar.iloc[i-1] + af * (extreme - sar.iloc[i-1])
                if high.iloc[i] > sar.iloc[i]:
                    trend = 1
                    sar.iloc[i] = extreme
                    extreme = high.iloc[i]
                    af = acceleration
                else:
                    if low.iloc[i] < extreme:
                        extreme = low.iloc[i]
                        af = min(af + acceleration, maximum)
        return sar

    @staticmethod
    def _kama(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        close = df['close'].values
        n = len(close)
        kama = np.zeros(n)
        kama[:period] = close[:period]
        for i in range(period, n):
            er = abs(close[i] - close[i-period]) / np.sum(np.abs(np.diff(close[i-period:i+1])))
            sc = (er * (2/(2+1) - 2/(30+1)) + 2/(30+1)) ** 2
            kama[i] = kama[i-1] + sc * (close[i] - kama[i-1])
        return pd.Series(kama, index=df.index)

    @staticmethod
    def _dema(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        return 2 * ema1 - ema2

    @staticmethod
    def _tema(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        ema1 = df['close'].ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        return 3 * ema1 - 3 * ema2 + ema3

    @staticmethod
    def _trima(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        half = (period + 1) // 2
        return df['close'].rolling(half).mean().rolling(half).mean()

    @staticmethod
    def _natr(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return (atr / df['close']) * 100

    @staticmethod
    def _cmo(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        delta = df['close'].diff()
        gain = delta.clip(lower=0).rolling(period).sum()
        loss = (-delta.clip(upper=0)).rolling(period).sum()
        return 100 * (gain - loss) / (gain + loss).replace(0, np.nan)

    @staticmethod
    def _apo(df, params):
        fast = int(params.get('fastperiod', params.get('fast', 12)))
        slow = int(params.get('slowperiod', params.get('slow', 26)))
        return df['close'].ewm(span=fast, adjust=False).mean() - df['close'].ewm(span=slow, adjust=False).mean()

    @staticmethod
    def _ppo(df, params):
        fast = int(params.get('fastperiod', params.get('fast', 12)))
        slow = int(params.get('slowperiod', params.get('slow', 26)))
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        return ((ema_fast - ema_slow) / ema_slow.replace(0, np.nan)) * 100

    @staticmethod
    def _aroon(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        high_idx = df['high'].rolling(period).apply(lambda x: x.argmax(), raw=True)
        low_idx = df['low'].rolling(period).apply(lambda x: x.argmin(), raw=True)
        aroon_up = ((period - high_idx) / period) * 100
        aroon_down = ((period - low_idx) / period) * 100
        output_index = params.get('output_index', 'down')
        return aroon_down if output_index == 'down' else aroon_up

    @staticmethod
    def _aroonosc(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        high_idx = df['high'].rolling(period).apply(lambda x: x.argmax(), raw=True)
        low_idx = df['low'].rolling(period).apply(lambda x: x.argmin(), raw=True)
        aroon_up = ((period - high_idx) / period) * 100
        aroon_down = ((period - low_idx) / period) * 100
        return aroon_up - aroon_down

    @staticmethod
    def _stddev(df, params):
        period = int(params.get('timeperiod', params.get('length', 5)))
        nbdev = float(params.get('nbdev', 1))
        return df['close'].rolling(period).std() * nbdev

    @staticmethod
    def _linearreg(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        def linreg(x):
            if len(x) < 2:
                return x.iloc[-1] if len(x) > 0 else 0
            return np.polyfit(range(len(x)), x, 1)[0] * (len(x) - 1) + np.polyfit(range(len(x)), x, 1)[1]
        return df['close'].rolling(period).apply(linreg, raw=True)

    @staticmethod
    def _tsf(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        def forecast(x):
            if len(x) < 2:
                return 0
            slope, intercept = np.polyfit(range(len(x)), x, 1)
            return slope * len(x) + intercept
        return df['close'].rolling(period).apply(forecast, raw=True)

    @staticmethod
    def _vwap(df, params):
        return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

    @staticmethod
    def _midpoint(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        return (df['close'].rolling(period).max() + df['close'].rolling(period).min()) / 2

    @staticmethod
    def _midprice(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        return (df['high'].rolling(period).max() + df['low'].rolling(period).min()) / 2

    @staticmethod
    def _typprice(df, params):
        return (df['high'] + df['low'] + df['close']) / 3

    @staticmethod
    def _avgprice(df, params):
        return (df['open'] + df['high'] + df['low'] + df['close']) / 4

    @staticmethod
    def _medprice(df, params):
        return (df['high'] + df['low']) / 2

    @staticmethod
    def _wclprice(df, params):
        return (df['high'] + df['low'] + 2 * df['close']) / 4

    @staticmethod
    def _bop(df, params):
        return (df['close'] - df['open']) / (df['high'] - df['low']).replace(0, np.nan)

    @staticmethod
    def _ultosc(df, params):
        p1 = int(params.get('timeperiod1', 7))
        p2 = int(params.get('timeperiod2', 14))
        p3 = int(params.get('timeperiod3', 28))
        close, low, high = df['close'], df['low'], df['high']
        bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        avg1 = bp.rolling(p1).sum() / tr.rolling(p1).sum().replace(0, np.nan)
        avg2 = bp.rolling(p2).sum() / tr.rolling(p2).sum().replace(0, np.nan)
        avg3 = bp.rolling(p3).sum() / tr.rolling(p3).sum().replace(0, np.nan)
        return 100 * (4 * avg1 + 2 * avg2 + avg3) / 7

    @staticmethod
    def _dx(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        plus_dm = df['high'].diff().clip(lower=0)
        minus_dm = df['low'].diff().clip(upper=0).abs()
        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        di_plus = 100 * (plus_dm.rolling(period).mean() / atr.replace(0, np.nan))
        di_minus = 100 * (minus_dm.rolling(period).mean() / atr.replace(0, np.nan))
        return 100 * ((di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan))

    @staticmethod
    def _plus_di(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        plus_dm = df['high'].diff().clip(lower=0)
        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return 100 * (plus_dm.rolling(period).mean() / atr.replace(0, np.nan))

    @staticmethod
    def _minus_di(df, params):
        period = int(params.get('timeperiod', params.get('length', 14)))
        minus_dm = df['low'].diff().clip(upper=0).abs()
        tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return 100 * (minus_dm.rolling(period).mean() / atr.replace(0, np.nan))

    @staticmethod
    def _ad(df, params):
        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']).replace(0, np.nan)
        return (clv * df['volume']).cumsum()

    @staticmethod
    def _adosc(df, params):
        fast = int(params.get('fastperiod', 3))
        slow = int(params.get('slowperiod', 10))
        clv = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']).replace(0, np.nan)
        ad = (clv * df['volume']).cumsum()
        return ad.ewm(span=fast, adjust=False).mean() - ad.ewm(span=slow, adjust=False).mean()

    @staticmethod
    def _trange(df, params):
        return pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift()).abs(), (df['low'] - df['close'].shift()).abs()], axis=1).max(axis=1)

    @staticmethod
    def _cdl_pattern(df, pattern_name):
        return pd.Series(0, index=df.index)

    @staticmethod
    def _apply_talib_func(df, func, name, params):
        output_index = params.pop('output_index', None)
        result = None
        executed = False
        for sig_args in [
            (df['open'], df['high'], df['low'], df['close']),
            (df['high'], df['low'], df['close'], df['volume']),
            (df['high'], df['low'], df['close']),
            (df['close'], df['volume']),
            (df['close'],),
            (df['high'], df['low']),
        ]:
            if not executed:
                try:
                    result = func(*sig_args, **params)
                    executed = True
                except Exception:
                    pass
        if not executed:
            raise ValueError(f"Failed to execute {name}")
        if isinstance(result, tuple):
            idx = 0
            if output_index is not None:
                mappings = {"BBANDS": {"upper": 0, "middle": 1, "lower": 2},
                           "MACD": {"macd": 0, "signal": 1, "hist": 2},
                           "STOCH": {"slowk": 0, "slowd": 1},
                           "STOCHRSI": {"fastk": 0, "fastd": 1},
                           "AROON": {"down": 0, "up": 1}}
                if name in mappings and output_index in mappings[name]:
                    idx = mappings[name][output_index]
            return pd.Series(result[idx], index=df.index) if 0 <= idx < len(result) else pd.Series(result[0], index=df.index)
        return pd.Series(result, index=df.index)

_has_talib = False
try:
    import talib
    _has_talib = True
except Exception:
    pass
