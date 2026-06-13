import pandas as pd
import numpy as np
import vectorbt as vbt
from .indicators import IndicatorManager

class BacktestEngine:
    """
    High-performance backtesting engine using VectorBT.
    Translates strategy rules into vectorized signals.
    Supports multi-condition logic and indicator-to-indicator comparisons.
    """
    
    def __init__(self):
        self.indicator_manager = IndicatorManager()

    def evaluate_condition(self, df: pd.DataFrame, cond: dict) -> pd.Series:
        """
        Evaluates a single condition, which can compare an indicator against a scalar value
        or against another indicator (e.g., SMA 10 crosses above SMA 30).
        """
        # 1. Evaluate LHS (Left-Hand Side)
        lhs_indicator = cond.get("indicator")
        if not lhs_indicator:
            return pd.Series(False, index=df.index)
        
        lhs_indicator = self.indicator_manager.normalize_name(lhs_indicator)
        lhs_params = cond.get("params", {})
        
        # Check if LHS is a direct column
        if lhs_indicator.upper() in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME"]:
            lhs_series = df[lhs_indicator.lower()]
        else:
            lhs_series = self.indicator_manager.apply_indicator(df, lhs_indicator, lhs_params)
            
        # 2. Evaluate RHS (Right-Hand Side)
        rhs_input = cond.get("value")
        if isinstance(rhs_input, dict) and "indicator" in rhs_input:
            # RHS is another indicator
            rhs_indicator = self.indicator_manager.normalize_name(rhs_input.get("indicator"))
            rhs_params = rhs_input.get("params", {})
            if rhs_indicator.upper() in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME"]:
                rhs_series = df[rhs_indicator.lower()]
            else:
                rhs_series = self.indicator_manager.apply_indicator(df, rhs_indicator, rhs_params)
        elif isinstance(rhs_input, (int, float)):
            # RHS is a scalar number
            rhs_series = float(rhs_input)
        elif isinstance(rhs_input, str):
            # Try to parse as number, or check if it matches a column
            if rhs_input.upper() in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME"]:
                rhs_series = df[rhs_input.lower()]
            else:
                try:
                    rhs_series = float(rhs_input)
                except ValueError:
                    raise ValueError(f"RHS value {rhs_input} must be a number or a valid column name")
        else:
            # Fallback/missing value
            rhs_series = 0.0

        # 3. Apply comparison operator
        op = cond.get("operator", "==")
        
        # Ensure we don't have NaN issues breaking comparisons
        # Fill NaNs with appropriate values or forward fill
        lhs_clean = lhs_series.ffill().fillna(0.0)
        if isinstance(rhs_series, pd.Series):
            rhs_clean = rhs_series.ffill().fillna(0.0)
        else:
            rhs_clean = rhs_series
            
        if op == "<":
            return lhs_clean < rhs_clean
        elif op == ">":
            return lhs_clean > rhs_clean
        elif op == "<=":
            return lhs_clean <= rhs_clean
        elif op == ">=":
            return lhs_clean >= rhs_clean
        elif op == "==":
            return lhs_clean == rhs_clean
        elif op == "!=":
            return lhs_clean != rhs_clean
        elif op in ["crosses_above", "cross_above"]:
            if isinstance(rhs_clean, pd.Series):
                prev_rhs = rhs_clean.shift(1).ffill().fillna(0.0)
            else:
                prev_rhs = rhs_clean
            return (lhs_clean > rhs_clean) & (lhs_clean.shift(1).ffill().fillna(0.0) <= prev_rhs)
        elif op in ["crosses_below", "cross_below"]:
            if isinstance(rhs_clean, pd.Series):
                prev_rhs = rhs_clean.shift(1).ffill().fillna(0.0)
            else:
                prev_rhs = rhs_clean
            return (lhs_clean < rhs_clean) & (lhs_clean.shift(1).ffill().fillna(0.0) >= prev_rhs)
            
        return pd.Series(False, index=df.index)

    def evaluate_rules(self, df: pd.DataFrame, rule_spec: dict) -> pd.Series:
        """
        Evaluates a set of rules. Supports a single condition or a nested list under 'conditions'.
        """
        if not rule_spec:
            return pd.Series(False, index=df.index)
            
        # Support multi-condition list
        if "conditions" in rule_spec:
            conditions = rule_spec["conditions"]
            if not conditions:
                return pd.Series(False, index=df.index)
                
            logical_op = rule_spec.get("logical_operator", "AND").upper()
            
            results = []
            for cond in conditions:
                try:
                    res = self.evaluate_condition(df, cond)
                    results.append(res)
                except Exception as e:
                    print(f"Error evaluating condition {cond}: {e}")
                    results.append(pd.Series(False, index=df.index))
                    
            if not results:
                return pd.Series(False, index=df.index)
                
            combined = results[0]
            for r in results[1:]:
                if logical_op == "OR":
                    combined = combined | r
                else:
                    combined = combined & r
            return combined
        else:
            # Fallback: single condition rule_spec
            return self.evaluate_condition(df, rule_spec)

    def run(self, df: pd.DataFrame, strategy_spec: dict) -> dict:
        """
        Runs a vectorized backtest on the given DataFrame.
        Supports entry/exit signals + stop loss and take profit.
        """
        # 0. Route to Options Engine if necessary
        instrument_type = strategy_spec.get('instrument_type', 'EQUITY').upper()
        if instrument_type == 'OPTION':
            # Local import to prevent circular dependency
            from .options_engine import OptionsEngine
            opt_engine = OptionsEngine()
            return opt_engine.run(df, strategy_spec)

        # Set index to time for VectorBT to handle timestamps correctly
        if 'time' in df.columns:
            df = df.set_index('time')

        # 1. Generate Signals
        entries = self.evaluate_rules(df, strategy_spec.get('entry', {}))
        exits = self.evaluate_rules(df, strategy_spec.get('exit', {}))

        # Ensure boolean type and align indexes
        entries = entries.astype(bool)
        exits = exits.astype(bool)

        # 2. Stop Loss and Take Profit
        # UI sends percentages (e.g. 2.0 for 2%), VectorBT expects fractions (0.02)
        stop_loss = strategy_spec.get('stop_loss')
        if stop_loss is not None and stop_loss > 0:
            stop_loss = float(stop_loss) / 100.0
        else:
            stop_loss = None
            
        take_profit = strategy_spec.get('take_profit')
        if take_profit is not None and take_profit > 0:
            take_profit = float(take_profit) / 100.0
        else:
            take_profit = None
        
        # 3. Run VectorBT Portfolio
        portfolio = vbt.Portfolio.from_signals(
            df['close'],
            entries,
            exits,
            sl_stop=stop_loss,
            tp_stop=take_profit,
            fees=float(strategy_spec.get('fees', 0.001)),
            slippage=float(strategy_spec.get('slippage', 0.001)),
            freq='D'
        )

        # 4. Extract Metrics
        stats = portfolio.stats()
        
        # Format returns to avoid NaN/Inf issues
        def safe_float(val, default=0.0):
            try:
                if pd.isna(val) or np.isinf(val):
                    return default
                return float(val)
            except:
                return default

        # Map index elements to ISO date strings for charts
        time_index = df.index
        
        # Build clean lists of value curve and drawdowns
        value_curve = portfolio.value()
        drawdown_curve = portfolio.drawdown()
        
        equity_curve = []
        for i, val in enumerate(value_curve):
            t_val = time_index[i]
            # convert timestamp/datetime to string
            if hasattr(t_val, 'strftime'):
                date_str = t_val.strftime('%Y-%m-%d')
            else:
                date_str = str(t_val).split(' ')[0]
            equity_curve.append({"date": date_str, "value": safe_float(val, 100.0)})
            
        drawdown_list = []
        for i, val in enumerate(drawdown_curve):
            t_val = time_index[i]
            if hasattr(t_val, 'strftime'):
                date_str = t_val.strftime('%Y-%m-%d')
            else:
                date_str = str(t_val).split(' ')[0]
            drawdown_list.append({"date": date_str, "value": safe_float(val * 100.0, 0.0)})

        # Parse trade records
        try:
            trades_df = portfolio.trades.records_readable
            trades_list = []
            for _, r in trades_df.iterrows():
                trades_list.append({
                    "id": int(r.get('Exit Trade Id', 0)),
                    "entry_date": str(r.get('Entry Timestamp')).split(' ')[0],
                    "exit_date": str(r.get('Exit Timestamp')).split(' ')[0],
                    "direction": r.get('Direction', 'Long'),
                    "entry_price": safe_float(r.get('Avg Entry Price')),
                    "exit_price": safe_float(r.get('Avg Exit Price')),
                    "pnl": safe_float(r.get('PnL')),
                    "pnl_pct": safe_float(r.get('Return')) * 100.0,
                    "size": safe_float(r.get('Size')),
                    "duration_days": str(r.get('Duration'))
                })
        except Exception as e:
            print(f"Error parsing trades: {e}")
            trades_list = []

        # Extended metrics calculation
        total_return = safe_float(stats.get('Total Return [%]'))
        max_dd = safe_float(stats.get('Max Drawdown [%]'))
        
        # Approximate CAGR
        days = len(value_curve)
        years = max(days / 252.0, 0.01)
        cagr = (((1 + (total_return / 100.0)) ** (1 / years)) - 1) * 100.0
        
        # Approximate Calmar
        calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0

        return {
            "total_return": total_return,
            "benchmark_return": safe_float(stats.get('Benchmark Return [%]')),
            "cagr": float(cagr),
            "calmar": float(calmar),
            "sharpe": safe_float(stats.get('Sharpe Ratio')),
            "sortino": safe_float(stats.get('Sortino Ratio')),
            "max_drawdown": max_dd,
            "win_rate": safe_float(stats.get('Win Rate [%]')),
            "profit_factor": safe_float(stats.get('Profit Factor')),
            "expectancy": safe_float(stats.get('Expectancy')),
            "equity_curve": equity_curve,
            "drawdown": drawdown_list,
            "trades": trades_list
        }

