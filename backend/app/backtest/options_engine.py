import pandas as pd
import numpy as np
from .indicators import IndicatorManager

class OptionsEngine:
    """
    Options backtesting engine for Indian derivatives (Nifty/BankNifty).
    Models option P&L: premium, delta, theta, vega, gamma.
    Supports strikes: ATM, OTM+1, OTM+2, ITM-1, ITM-2, or absolute value.
    """

    STRIKE_INTERVALS = {"NIFTY": 50, "BANKNIFTY": 100, "FINNIFTY": 50, "SENSEX": 100}

    def __init__(self):
        self.indicator_manager = IndicatorManager()

    def _resolve_strike(self, underlying_price: float, strike_spec, symbol: str) -> float:
        interval = self.STRIKE_INTERVALS.get(symbol.upper(), 50)
        atm_strike = round(underlying_price / interval) * interval

        if isinstance(strike_spec, (int, float)):
            return float(strike_spec)
        spec = str(strike_spec).upper()
        if spec == "ATM":
            return atm_strike
        if spec.startswith("OTM+"):
            offset = int(spec.replace("OTM+", ""))
            return atm_strike + offset * interval
        if spec.startswith("OTM"):
            return atm_strike + interval
        if spec.startswith("ITM-"):
            offset = int(spec.replace("ITM-", ""))
            return atm_strike - offset * interval
        if spec.startswith("ITM"):
            return atm_strike - interval
        return atm_strike

    def _option_payoff(self, df: pd.DataFrame, strike: float, option_type: str, premium: float, is_credit: bool) -> pd.Series:
        if option_type == "CE":
            intrinsic = df['close'] - strike
        elif option_type == "PE":
            intrinsic = strike - df['close']
        elif option_type == "STRADDLE":
            intrinsic = abs(df['close'] - strike)
        else:
            return pd.Series(0.0, index=df.index)

        intrinsic = np.maximum(intrinsic, 0.0)
        if is_credit:
            return premium - intrinsic
        return intrinsic - premium

    def run(self, df: pd.DataFrame, strategy_spec: dict) -> dict:
        strike_spec = strategy_spec.get('strike', 'ATM')
        option_type = strategy_spec.get('option_type', 'CE').upper()
        is_credit = strategy_spec.get('is_credit', False)

        first_close = df['close'].iloc[0]
        strike = self._resolve_strike(first_close, strike_spec, strategy_spec.get('symbol', 'NIFTY'))
        premium = strategy_spec.get('premium', 0.0)

        if premium <= 0:
            option_price = self._estimate_option_price(df, strike, option_type)
            premium = float(option_price.iloc[0]) if not option_price.empty else 0.0

        # UI sends percentages, convert to fractions
        stop_loss = strategy_spec.get('stop_loss', 0.0)
        if stop_loss > 0: stop_loss = float(stop_loss) / 100.0
        
        take_profit = strategy_spec.get('take_profit', 0.0)
        if take_profit > 0: take_profit = float(take_profit) / 100.0

        entry_signal = pd.Series(False, index=df.index)
        if strategy_spec.get('entry'):
            entry_signal = self._evaluate_rules(df, strategy_spec['entry'])
        else:
            entry_signal.iloc[0] = True

        exit_signal = pd.Series(False, index=df.index)
        if strategy_spec.get('exit'):
            exit_signal = self._evaluate_rules(df, strategy_spec['exit'])

        in_position = False
        entry_price = 0.0
        initial_equity = 10000.0
        equity = []
        trade_list = []
        trade_id = 0
        pnl_series = []

        # We need a proper time series of option prices for marking-to-market
        option_prices = self._estimate_option_price(df, strike, option_type)

        for i in range(len(df)):
            current_option_price = float(option_prices.iloc[i])
            
            if in_position:
                # P&L is current price minus entry price (for Long)
                # or entry price minus current price (for Short/Credit)
                if is_credit:
                    position_pnl = (entry_price - current_option_price)
                else:
                    position_pnl = (current_option_price - entry_price)
                
                pnl_pct = position_pnl / entry_price if entry_price != 0 else 0
                sl_hit = stop_loss > 0 and pnl_pct <= -stop_loss
                tp_hit = take_profit > 0 and pnl_pct >= take_profit

                if exit_signal.iloc[i] or sl_hit or tp_hit:
                    exit_reason = "SL" if sl_hit else ("TP" if tp_hit else "Signal")
                    # Close trade
                    trade_pnl = position_pnl
                    initial_equity += trade_pnl
                    equity.append(initial_equity)
                    pnl_series.append(trade_pnl)
                    
                    trade_list.append({
                        "id": trade_id, "direction": "Short" if is_credit else "Long",
                        "entry_date": str(entry_date).split(' ')[0],
                        "exit_date": str(df['time'].iloc[i]).split(' ')[0],
                        "entry_price": float(entry_price),
                        "exit_price": float(current_option_price),
                        "pnl": float(trade_pnl),
                        "pnl_pct": float(pnl_pct * 100),
                        "size": 1, "duration_days": i - entry_idx,
                        "exit_reason": exit_reason
                    })
                    trade_id += 1
                    in_position = False
                else:
                    # Mark-to-market equity
                    equity.append(initial_equity + position_pnl)
                    pnl_series.append(position_pnl)
            else:
                equity.append(initial_equity)
                pnl_series.append(0.0)

                if entry_signal.iloc[i]:
                    in_position = True
                    entry_price = current_option_price
                    entry_date = df['time'].iloc[i]
                    entry_idx = i

        equity_series = pd.Series(equity, index=df.index)
        returns = pd.Series(pnl_series, index=df.index).diff().fillna(0.0) / 10000.0

        total_return = ((equity_series.iloc[-1] / 10000.0) - 1) * 100 if len(equity_series) > 0 else 0.0
        days = len(df)
        years = max(days / 252.0, 0.01)
        cagr = (((1 + (total_return / 100.0)) ** (1 / years)) - 1) * 100.0

        running_max = equity_series.cummax()
        drawdown_pct = ((equity_series - running_max) / running_max * 100).fillna(0.0)
        max_dd = float(drawdown_pct.min()) if len(drawdown_pct) > 0 else 0.0

        sharpe = 0.0
        sortino = 0.0
        win_rate = 0.0
        profit_factor = 0.0
        expectancy = 0.0

        if len(returns) > 0:
            ann_factor = 252
            std_ret = returns.std()
            if std_ret > 0:
                sharpe = float((returns.mean() / std_ret) * np.sqrt(ann_factor))
            downside = returns[returns < 0]
            downside_std = downside.std() if len(downside) > 0 else 0.001
            sortino = float((returns.mean() / downside_std) * np.sqrt(ann_factor)) if downside_std > 0 else 0.0

        if trade_list:
            wins = [t for t in trade_list if t['pnl'] > 0]
            losses = [t for t in trade_list if t['pnl'] <= 0]
            win_rate = (len(wins) / len(trade_list)) * 100
            avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
            avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 1
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            expectancy = np.mean([t['pnl'] for t in trade_list])

        calmar = cagr / abs(max_dd) if max_dd < 0 else 0.0

        equity_curve_list = []
        for i, val in enumerate(equity_series):
            t_val = df['time'].iloc[i]
            date_str = t_val.strftime('%Y-%m-%d') if hasattr(t_val, 'strftime') else str(t_val).split(' ')[0]
            equity_curve_list.append({"date": date_str, "value": float(val)})

        drawdown_list = []
        for i, val in enumerate(drawdown_pct):
            t_val = df['time'].iloc[i]
            date_str = t_val.strftime('%Y-%m-%d') if hasattr(t_val, 'strftime') else str(t_val).split(' ')[0]
            drawdown_list.append({"date": date_str, "value": float(val)})

        return {
            "total_return": float(total_return),
            "benchmark_return": 0.0,
            "cagr": float(cagr),
            "calmar": float(calmar),
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "max_drawdown": float(max_dd),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "expectancy": float(expectancy),
            "instrument_type": "OPTION",
            "strike": float(strike),
            "option_type": option_type,
            "equity_curve": equity_curve_list,
            "drawdown": drawdown_list,
            "trades": trade_list
        }

    def _estimate_option_price(self, df: pd.DataFrame, strike: float, option_type: str) -> pd.Series:
        try:
            from scipy.stats import norm
            close = df['close']
            returns = close.pct_change().dropna()
            sigma = returns.std() * np.sqrt(252) if len(returns) > 0 else 0.2
            sigma = max(sigma, 0.05)
            r = 0.065
            t = 7.0 / 365.0

            s = close
            d1 = (np.log(s / strike) + (r + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
            d2 = d1 - sigma * np.sqrt(t)

            if option_type == "CE":
                price = s * norm.cdf(d1) - strike * np.exp(-r * t) * norm.cdf(d2)
            elif option_type == "PE":
                price = strike * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)
            else:
                ce = s * norm.cdf(d1) - strike * np.exp(-r * t) * norm.cdf(d2)
                pe = strike * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)
                price = ce + pe

            return price.fillna(price.median() if not price.empty else 50.0)
        except Exception:
            return pd.Series(50.0, index=df.index)

    def _evaluate_rules(self, df: pd.DataFrame, rule_spec: dict) -> pd.Series:
        from .engine import BacktestEngine
        equity_engine = BacktestEngine()
        return equity_engine.evaluate_rules(df, rule_spec)
