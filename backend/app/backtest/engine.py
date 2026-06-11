import pandas as pd
import numpy as np
import vectorbt as vbt
from .indicators import IndicatorManager

class BacktestEngine:
    """
    High-performance backtesting engine using VectorBT.
    Translates strategy rules into vectorized signals.
    """
    
    def __init__(self):
        self.indicator_manager = IndicatorManager()

    def run(self, df: pd.DataFrame, strategy_spec: dict) -> dict:
        """
        Runs a vectorized backtest.
        
        Args:
            df: OHLCV DataFrame
            strategy_spec: {
                "entry": {"indicator": "RSI", "operator": "<", "value": 30},
                "exit": {"indicator": "RSI", "operator": ">", "value": 70},
                "fees": 0.001,
                "slippage": 0.001
            }
        """
        # 1. Calculate Indicators
        entry_indicator = self.indicator_manager.apply_indicator(
            df, 
            strategy_spec['entry']['indicator'], 
            strategy_spec['entry'].get('params', {})
        )
        
        exit_indicator = self.indicator_manager.apply_indicator(
            df, 
            strategy_spec['exit']['indicator'], 
            strategy_spec['exit'].get('params', {})
        )
        
        # 2. Generate Signals
        # Entry Logic
        if strategy_spec['entry']['operator'] == "<":
            entries = entry_indicator < strategy_spec['entry']['value']
        elif strategy_spec['entry']['operator'] == ">":
            entries = entry_indicator > strategy_spec['entry']['value']
        else:
            entries = entry_indicator == strategy_spec['entry']['value']
            
        # Exit Logic
        if strategy_spec['exit']['operator'] == ">":
            exits = exit_indicator > strategy_spec['exit']['value']
        elif strategy_spec['exit']['operator'] == "<":
            exits = exit_indicator < strategy_spec['exit']['value']
        else:
            exits = exit_indicator == strategy_spec['exit']['value']

        # 3. Run VectorBT Portfolio
        portfolio = vbt.Portfolio.from_signals(
            df['close'],
            entries,
            exits,
            fees=strategy_spec.get('fees', 0.001),
            slippage=strategy_spec.get('slippage', 0.001),
            freq='D' # Default to Daily, should be dynamic based on data
        )

        # 4. Extract Metrics
        stats = portfolio.stats()
        
        return {
            "total_return": float(stats['Total Return [%]']),
            "benchmark_return": float(stats['Benchmark Return [%]']),
            "sharpe": float(stats['Sharpe Ratio']),
            "sortino": float(stats['Sortino Ratio']),
            "max_drawdown": float(stats['Max Drawdown [%]']),
            "win_rate": float(stats['Win Rate [%]']),
            "profit_factor": float(stats['Profit Factor']),
            "expectancy": float(stats['Expectancy']),
            "equity_curve": [
                {"date": str(d), "value": float(v)} 
                for d, v in portfolio.value().items()
            ],
            "drawdown": [
                {"date": str(d), "value": float(v)} 
                for d, v in portfolio.drawdown().items()
            ],
            "trades": portfolio.trades.records_readable.to_dict(orient='records')
        }
