import talib
import pandas as pd
import numpy as np
from .indicator_db import INDICATORS_DB

class IndicatorManager:
    """
    Manages 100+ TA-Lib indicators for backtesting.
    Provides a consistent interface for the engine to request technical data.
    """
    
    @staticmethod
    def get_indicators_list():
        """Returns the complete structured indicator database."""
        return INDICATORS_DB

    @staticmethod
    def apply_indicator(df: pd.DataFrame, name: str, params: dict = None) -> pd.Series:
        """
        Applies a TA-Lib or custom indicator to a DataFrame.
        """
        if params is None:
            params = {}
            
        name = name.upper()
        
        # 1. Custom & Options Indicators
        if name == "VWAP":
            pv = df['close'] * df['volume']
            return pv.cumsum() / df['volume'].cumsum()

        # Options Greeks (Assuming columns exist or need calculation)
        if name in ["DELTA", "GAMMA", "THETA", "VEGA", "IV"]:
            col_name = name.lower()
            if col_name in df.columns:
                return df[col_name]
            # Fallback to zero if not provided in the data stream
            return pd.Series(0.0, index=df.index)
            
        # 2. Look up TA-Lib function
        func = getattr(talib, name, None)
        if not func:
            raise ValueError(f"Indicator {name} not found in TA-Lib or custom indicators.")
            
        # Extract output index mapping if a multiple-output indicator is queried
        # (e.g., MACD returns macd, signal, hist; BBANDS returns upper, middle, lower)
        output_index = params.pop('output_index', None)
        
        # 3. Dynamic signatures execution: try executing in order of parameter counts
        result = None
        executed = False
        
        # Signature A: (open, high, low, close) - standard patterns and price transforms
        if not executed:
            try:
                result = func(df['open'], df['high'], df['low'], df['close'], **params)
                executed = True
            except Exception:
                pass
                
        # Signature B: (high, low, close, volume) - MFI, AD, ADOSC
        if not executed:
            try:
                result = func(df['high'], df['low'], df['close'], df['volume'], **params)
                executed = True
            except Exception:
                pass
                
        # Signature C: (high, low, close) - ADX, ATR, CCI, WILLR, NATR
        if not executed:
            try:
                result = func(df['high'], df['low'], df['close'], **params)
                executed = True
            except Exception:
                pass
                
        # Signature D: (close, volume) - OBV
        if not executed:
            try:
                result = func(df['close'], df['volume'], **params)
                executed = True
            except Exception:
                pass
                
        # Signature E: (close) - SMA, EMA, RSI, STDDEV, TSF, KAMA
        if not executed:
            try:
                result = func(df['close'], **params)
                executed = True
            except Exception:
                pass
                
        # Signature F: (high, low) - SAR, AROON
        if not executed:
            try:
                result = func(df['high'], df['low'], **params)
                executed = True
            except Exception:
                pass

        if not executed:
            raise ValueError(f"Failed to execute TA-Lib indicator {name}. Check that the parameter values are valid.")

        # 4. Handle multiple-output tuple results (like BBANDS, MACD, STOCH)
        if isinstance(result, tuple):
            mapped_idx = 0
            if output_index is not None:
                if isinstance(output_index, int):
                    mapped_idx = output_index
                elif isinstance(output_index, str):
                    output_str = output_index.lower()
                    if name == "BBANDS":
                        mapping = {"upper": 0, "middle": 1, "lower": 2}
                        mapped_idx = mapping.get(output_str, 1)
                    elif name == "MACD":
                        mapping = {"macd": 0, "signal": 1, "hist": 2}
                        mapped_idx = mapping.get(output_str, 0)
                    elif name == "STOCH":
                        mapping = {"slowk": 0, "slowd": 1}
                        mapped_idx = mapping.get(output_str, 0)
                    elif name == "STOCHRSI":
                        mapping = {"fastk": 0, "fastd": 1}
                        mapped_idx = mapping.get(output_str, 0)
                    elif name == "AROON":
                        mapping = {"down": 0, "up": 1}
                        mapped_idx = mapping.get(output_str, 0)
            
            # Extract the correct array from the tuple
            if 0 <= mapped_idx < len(result):
                return pd.Series(result[mapped_idx], index=df.index)
            return pd.Series(result[0], index=df.index)
            
        return pd.Series(result, index=df.index)

