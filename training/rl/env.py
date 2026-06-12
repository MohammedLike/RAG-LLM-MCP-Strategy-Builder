"""
Reinforcement Learning environment for strategy optimization.
Wraps the backtest engine as a Gymnasium environment.
State: Market regime features (volatility, trend, volume)
Action: Strategy parameter adjustments (indicator periods, entry/exit thresholds)
Reward: Sharpe ratio over evaluation window
"""
import numpy as np
import pandas as pd
from gymnasium import Env, spaces
from gymnasium.envs.registration import register

try:
    from backend.app.backtest.engine import BacktestEngine
    from backend.app.market.provider_yfinance import YFinanceProvider
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from backend.app.backtest.engine import BacktestEngine
    from backend.app.market.provider_yfinance import YFinanceProvider


class BacktestEnv(Env):
    """
    Gymnasium environment for strategy optimization.

    Observation space (5-dim):
        [volatility (ATR/close), trend_strength (ADX), momentum (ROC),
         volume_change, current_sharpe]

    Action space (3-dim continuous in [-1, 1]):
        [entry_threshold_offset, exit_threshold_offset, period_adjustment]
    """

    def __init__(self, symbol: str = "NIFTY", period: str = "5y",
                 window_days: int = 252, eval_days: int = 63):
        super().__init__()

        self.symbol = symbol
        self.period = period
        self.window_days = window_days
        self.eval_days = eval_days
        self.engine = BacktestEngine()
        self.provider = YFinanceProvider()

        self.observation_space = spaces.Box(low=-10, high=10, shape=(5,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)

        self.df = None
        self.current_idx = 0
        self.max_idx = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                from ..backend.app.market.provider_yfinance import YFinanceProvider
                import yfinance as yf
                ticker = "^NSEI" if self.symbol == "NIFTY" else f"{self.symbol}.NS"
                t = yf.Ticker(ticker)
                df = t.history(period=self.period, interval="1d")
                df = df.reset_index()
                df.columns = [c.lower() for c in df.columns]
                df.columns = ['time' if c in ('date', 'datetime') else c for c in df.columns]
                self.df = df
            else:
                end = pd.Timestamp.now()
                start = end - pd.Timedelta(days={"1y": 365, "2y": 730, "5y": 1825, "8y": 2920}[self.period])
                self.df = loop.run_until_complete(
                    self.provider.get_ohlcv(self.symbol, "1d", start, end)
                )
        except Exception:
            import yfinance as yf
            ticker = "^NSEI" if self.symbol == "NIFTY" else f"{self.symbol}.NS"
            t = yf.Ticker(ticker)
            df = t.history(period=self.period, interval="1d")
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            df.columns = ['time' if c in ('date', 'datetime') else c for c in df.columns]
            self.df = df

        if self.df is None or len(self.df) < self.window_days + self.eval_days:
            raise ValueError(f"Not enough data. Need {self.window_days + self.eval_days} rows.")

        self.current_idx = np.random.randint(0, len(self.df) - self.window_days - self.eval_days)
        self.max_idx = len(self.df) - self.window_days - self.eval_days

        return self._get_obs(), {}

    def _get_obs(self):
        window = self.df.iloc[self.current_idx:self.current_idx + self.min(self.window_days, 60)]
        close = window['close']
        high = window['high']
        low = window['low']
        volume = window['volume']

        atr = (high - low).mean()
        volatility = atr / close.mean() if close.mean() > 0 else 0

        roc = ((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) if close.iloc[0] > 0 else 0
        vol_change = (volume.iloc[-1] - volume.iloc[0]) / volume.iloc[0] if volume.iloc[0] > 0 else 0

        sharpe = close.pct_change().mean() / close.pct_change().std() * np.sqrt(252) if close.pct_change().std() > 0 else 0

        return np.array([volatility, roc, roc, vol_change, sharpe], dtype=np.float32)

    def step(self, action):
        entry_adj = float(action[0]) * 10
        exit_adj = float(action[1]) * 10
        period_adj = int(float(action[2]) * 20)

        rsi_period = max(5, min(50, 14 + period_adj))
        entry_threshold = max(5, min(50, 30 + entry_adj))
        exit_threshold = max(50, min(95, 70 + exit_adj))

        strategy_spec = {
            "entry": {
                "conditions": [{"indicator": "RSI", "params": {"timeperiod": rsi_period},
                                "operator": "<", "value": entry_threshold}],
                "logical_operator": "AND"
            },
            "exit": {
                "conditions": [{"indicator": "RSI", "params": {"timeperiod": rsi_period},
                                "operator": ">", "value": exit_threshold}],
                "logical_operator": "AND"
            }
        }

        eval_df = self.df.iloc[self.current_idx:self.current_idx + self.eval_days]
        if len(eval_df) < 20:
            return self._get_obs(), 0, True, False, {}

        try:
            result = self.engine.run(eval_df.copy(), strategy_spec)
            reward = result.get("sharpe", 0)

            if np.isnan(reward) or np.isinf(reward):
                reward = -1.0

            if result.get("max_drawdown", 0) < -30:
                reward -= 0.5
            if result.get("win_rate", 0) > 60:
                reward += 0.3
            if result.get("profit_factor", 1) > 2:
                reward += 0.2
        except Exception:
            reward = -2.0

        self.current_idx += self.eval_days
        terminated = self.current_idx >= self.max_idx

        return self._get_obs(), float(reward), terminated, False, {"sharpe": reward}

    def min(self, a, b):
        return a if a < b else b
