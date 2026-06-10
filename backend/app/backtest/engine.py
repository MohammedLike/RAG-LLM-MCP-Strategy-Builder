import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self):
        pass

    def run(self, strategy_spec: dict, symbol: str, period: str) -> dict:
        """
        Takes strategy JSON spec, generates signals and runs backtest.
        For this prototype, it returns mock data.
        """
        # Mocking the output
        dates = pd.date_range(start="2025-01-01", periods=100)
        equity_curve = np.cumsum(np.random.normal(0, 1, 100)) + 100
        
        return {
            "sharpe": 1.25,
            "sortino": 1.8,
            "calmar": 0.9,
            "max_drawdown": -0.12,
            "equity_curve": [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in zip(dates, equity_curve)]
        }
