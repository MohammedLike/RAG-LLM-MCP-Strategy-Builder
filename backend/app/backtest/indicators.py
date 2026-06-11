import talib
import pandas as pd
import numpy as np

class IndicatorManager:
    """
    Manages 100+ TA-Lib indicators for backtesting.
    Provides a consistent interface for the engine to request technical data.
    """
    
    @staticmethod
    def get_indicators_list():
        """Returns a list of all available TA-Lib functions."""
        return talib.get_functions()

    @staticmethod
    def apply_indicator(df: pd.DataFrame, name: str, params: dict = None) -> pd.Series:
        """
        Applies a TA-Lib indicator to a DataFrame.
        Expected columns: 'open', 'high', 'low', 'close', 'volume'
        """
        if params is None:
            params = {}
            
        name = name.upper()
        
        # Mapping common indicator requests to TA-Lib functions
        # This can be expanded to cover the full 100+ functions
        
        # Momentum Indicators
        if name == "RSI":
            return talib.RSI(df['close'], timeperiod=params.get('timeperiod', 14))
        elif name == "MACD":
            macd, macdsignal, macdhist = talib.MACD(
                df['close'], 
                fastperiod=params.get('fastperiod', 12), 
                slowperiod=params.get('slowperiod', 26), 
                signalperiod=params.get('signalperiod', 9)
            )
            return macd # Return main line by default, can be customized
        elif name == "ADX":
            return talib.ADX(df['high'], df['low'], df['close'], timeperiod=params.get('timeperiod', 14))
        
        # Volatility Indicators
        elif name == "BBANDS":
            upper, middle, lower = talib.BBANDS(
                df['close'], 
                timeperiod=params.get('timeperiod', 5), 
                nbdevup=params.get('nbdevup', 2), 
                nbdevdn=params.get('nbdevdn', 2)
            )
            return middle # Return middle band by default
            
        # Overlap Studies
        elif name == "SMA":
            return talib.SMA(df['close'], timeperiod=params.get('timeperiod', 30))
        elif name == "EMA":
            return talib.EMA(df['close'], timeperiod=params.get('timeperiod', 30))
        elif name == "VWAP":
            # VWAP isn't in standard TA-Lib, calculate manually or use pandas-ta
            pv = df['close'] * df['volume']
            return pv.cumsum() / df['volume'].cumsum()
            
        # Generic fallback for any other TA-Lib function
        func = getattr(talib, name, None)
        if func:
            # Most TA-Lib functions take (close, timeperiod)
            try:
                return func(df['close'], **params)
            except:
                # Some take (high, low, close)
                try:
                    return func(df['high'], df['low'], df['close'], **params)
                except Exception as e:
                    raise ValueError(f"Indicator {name} failed: {str(e)}")
        
        raise ValueError(f"Indicator {name} not supported or not found in TA-Lib.")
