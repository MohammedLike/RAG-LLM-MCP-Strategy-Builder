"""
Evaluate trained RL agent performance against baseline strategies.
"""
import sys, os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from training.rl.train import evaluate_agent
    from training.rl.env import BacktestEnv
except ImportError:
    from train import evaluate_agent, train_agent
    from env import BacktestEnv


def benchmark_comparison(symbol: str = "NIFTY"):
    """
    Compare RL agent vs standard RSI strategy baselines.
    """
    print(f"\n=== Benchmark Comparison for {symbol} ===\n")

    baselines = {
        "RSI(14) <30 / >70": lambda: {"entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "<", "value": 30}], "logical_operator": "AND"},
                                        "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 14}, "operator": ">", "value": 70}], "logical_operator": "AND"}},
        "RSI(7) <25 / >75": lambda: {"entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 7}, "operator": "<", "value": 25}], "logical_operator": "AND"},
                                      "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 7}, "operator": ">", "value": 75}], "logical_operator": "AND"}},
        "RSI(21) <35 / >65": lambda: {"entry": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 21}, "operator": "<", "value": 35}], "logical_operator": "AND"},
                                       "exit": {"conditions": [{"indicator": "RSI", "params": {"timeperiod": 21}, "operator": ">", "value": 65}], "logical_operator": "AND"}},
    }

    print(f"{'Strategy':<25} {'Sharpe':<10} {'Return%':<10} {'MaxDD%':<10} {'WinRate%':<10}")
    print("-" * 65)

    for name, spec_fn in baselines.items():
        try:
            import asyncio
            from backend.app.backtest.engine import BacktestEngine
            from backend.app.market.provider_yfinance import YFinanceProvider

            engine = BacktestEngine()
            provider = YFinanceProvider()
            import yfinance as yf
            ticker = "^NSEI" if symbol == "NIFTY" else f"{symbol}.NS"
            t = yf.Ticker(ticker)
            df = t.history(period="3y", interval="1d")
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            df.columns = ['time' if c in ('date','datetime') else c for c in df.columns]
            df['symbol'] = symbol

            result = engine.run(df, spec_fn())
            sharpe = result.get("sharpe", 0)
            ret = result.get("total_return", 0)
            dd = result.get("max_drawdown", 0)
            wr = result.get("win_rate", 0)
            print(f"{name:<25} {sharpe:<10.2f} {ret:<10.2f} {dd:<10.2f} {wr:<10.2f}")
        except Exception as e:
            print(f"{name:<25} ERROR: {e}")

    print("\nNote: Run 'python -m training.rl.train' first to train the RL agent,")
    print("then use evaluate_agent() to compare its performance.")


if __name__ == "__main__":
    benchmark_comparison("NIFTY")
