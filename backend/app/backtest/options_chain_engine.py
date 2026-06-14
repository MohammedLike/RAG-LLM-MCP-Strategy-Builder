"""Backtest NIFTY options using historical options_chain snapshots from Postgres."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text

from ..db.options_chain_store import fetch_chain_series
from ..db.session import async_session, is_db_available
from .indicators import IndicatorManager


class OptionsChainBacktestEngine:
    STRIKE_INTERVALS = {"NIFTY": 50, "BANKNIFTY": 100, "FINNIFTY": 50}

    async def run(self, config: dict) -> dict:
        symbol = (config.get("symbol") or "NIFTY").upper()
        start = _parse_date(config.get("start_date"))
        end = _parse_date(config.get("end_date"))
        if not start or not end or start > end:
            return {"error": "Invalid start_date / end_date"}

        option_type = (config.get("option_type") or "CE").upper()
        strike_spec = config.get("strike") or "ATM"
        expiry_mode = config.get("expiry_mode") or "nearest_weekly"
        fixed_expiry = _parse_date(config.get("expiry")) if config.get("expiry") else None

        chain = await fetch_chain_series(
            symbol, start, end, None, option_type,
            expiry=fixed_expiry, expiry_mode=expiry_mode, strike_spec=strike_spec,
        )
        if len(chain) < 2:
            return {
                "error": (
                    f"No option chain data for {symbol} {option_type} ({strike_spec}) "
                    f"between {start} and {end}. Check database ingest."
                )
            }

        strike = float(chain[0]["strike"])

        df = pd.DataFrame(chain)
        df["time"] = pd.to_datetime(df["date"])
        df["close"] = df["close"].astype(float)
        df["premium"] = df["close"]

        underlying = await self._load_underlying(symbol, start, end)
        if underlying is not None and len(underlying) == len(df):
            df["underlying"] = underlying["close"].values
        elif "underlying" in df.columns:
            df["underlying"] = df["underlying"].ffill()
        else:
            df["underlying"] = df["close"]

        entry_signal = self._entry_signal(df, config.get("entry_condition") or "always")
        exit_signal = self._exit_signal(df, config.get("exit_condition") or "signal")

        result = self._simulate(
            df,
            entry_signal,
            exit_signal,
            config,
            symbol=symbol,
            strike=strike,
            option_type=option_type,
        )
        result.update({
            "symbol": symbol,
            "period": f"{start} to {end}",
            "data_source": "options_chain_db",
            "data_rows": len(df),
            "data_start": str(start),
            "data_end": str(end),
            "strike": strike,
            "option_type": option_type,
            "expiry_mode": expiry_mode,
            "instrument_type": "OPTION",
            "run_name": config.get("run_name"),
        })
        result["ohlcv"] = [
            {
                "time": row["date"],
                "open": float(row.get("open") or row["close"]),
                "high": float(row.get("high") or row["close"]),
                "low": float(row.get("low") or row["close"]),
                "close": float(row["close"]),
            }
            for _, row in df.iterrows()
        ]
        return result

    async def _load_underlying(self, symbol: str, start: date, end: date) -> pd.DataFrame | None:
        if not is_db_available():
            return None
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT time::date AS d, close
                        FROM ohlcv
                        WHERE symbol = :symbol AND resolution = '1d'
                          AND time::date BETWEEN :start AND :end
                        ORDER BY time
                        """
                    ),
                    {"symbol": symbol, "start": start, "end": end},
                )
            ).mappings().all()
        if not rows:
            return None
        return pd.DataFrame([{"date": str(r["d"]), "close": float(r["close"])} for r in rows])

    def _ind_series(self, series: pd.Series, name: str, params: dict) -> pd.Series:
        frame = pd.DataFrame({"close": series.astype(float)})
        return IndicatorManager.apply_indicator(frame, name, params)

    def _entry_signal(self, df: pd.DataFrame, condition: str) -> pd.Series:
        cond = (condition or "always").lower()
        if cond == "always":
            out = pd.Series(False, index=df.index)
            out.iloc[0] = True
            return out

        und = df["underlying"].astype(float)
        if cond == "rsi_below_30":
            return self._ind_series(und, "RSI", {"timeperiod": 14}) < 30
        if cond == "rsi_above_70":
            return self._ind_series(und, "RSI", {"timeperiod": 14}) > 70
        if cond == "ema_cross_up":
            e50 = self._ind_series(und, "EMA", {"timeperiod": 50})
            e200 = self._ind_series(und, "EMA", {"timeperiod": 200})
            return (e50 > e200) & (e50.shift(1) <= e200.shift(1))
        if cond == "ema_cross_down":
            e50 = self._ind_series(und, "EMA", {"timeperiod": 50})
            e200 = self._ind_series(und, "EMA", {"timeperiod": 200})
            return (e50 < e200) & (e50.shift(1) >= e200.shift(1))
        out = pd.Series(False, index=df.index)
        out.iloc[0] = True
        return out

    def _exit_signal(self, df: pd.DataFrame, condition: str) -> pd.Series:
        cond = (condition or "signal").lower()
        if cond in ("sl_tp", "none"):
            return pd.Series(False, index=df.index)
        und = df["underlying"].astype(float)
        if cond == "rsi_above_70":
            return self._ind_series(und, "RSI", {"timeperiod": 14}) > 70
        if cond == "rsi_below_30":
            return self._ind_series(und, "RSI", {"timeperiod": 14}) < 30
        if cond == "expiry":
            exp = pd.to_datetime(df["expiry"])
            t = pd.to_datetime(df["date"])
            return t >= exp
        return pd.Series(False, index=df.index)

    def _simulate(
        self,
        df: pd.DataFrame,
        entry_signal: pd.Series,
        exit_signal: pd.Series,
        config: dict,
        *,
        symbol: str,
        strike: float,
        option_type: str,
    ) -> dict:
        is_credit = bool(config.get("is_credit", False))
        max_trades_day = int(config.get("max_trades_per_day") or 1)

        txn_sl = _threshold(config.get("txn_stop_loss"), config.get("txn_stop_loss_unit", "%"))
        txn_tp = _threshold(config.get("txn_take_profit"), config.get("txn_take_profit_unit", "%"))
        daily_sl = float(config.get("daily_stop_loss") or 0)
        daily_tp = float(config.get("daily_take_profit") or 0)

        initial_equity = float(config.get("initial_capital") or 100000)
        lot_size = int(config.get("lot_size") or 50)
        equity = initial_equity
        equity_curve = []
        drawdown_curve = []
        trades = []
        trade_id = 0
        in_position = False
        entry_price = 0.0
        entry_date = None
        entry_idx = 0
        day_pnl = 0.0
        day_trades = 0
        current_day = None

        for i in range(len(df)):
            row = df.iloc[i]
            price = float(row["close"])
            day = str(row["date"])
            if current_day != day:
                current_day = day
                day_pnl = 0.0
                day_trades = 0

            if in_position:
                pnl_pts = (entry_price - price) if is_credit else (price - entry_price)
                pnl_inr = pnl_pts * lot_size
                pnl_pct = (pnl_pts / entry_price * 100) if entry_price else 0

                sl_hit = _hit_sl(txn_sl, pnl_pct, pnl_inr, pnl_pts)
                tp_hit = _hit_tp(txn_tp, pnl_pct, pnl_inr, pnl_pts)
                daily_sl_hit = daily_sl > 0 and day_pnl + pnl_inr <= -daily_sl
                daily_tp_hit = daily_tp > 0 and day_pnl + pnl_inr >= daily_tp

                if exit_signal.iloc[i] or sl_hit or tp_hit or daily_sl_hit or daily_tp_hit:
                    reason = "Signal"
                    if sl_hit:
                        reason = "SL"
                    elif tp_hit:
                        reason = "TP"
                    elif daily_sl_hit:
                        reason = "Daily SL"
                    elif daily_tp_hit:
                        reason = "Daily TP"

                    equity += pnl_inr
                    day_pnl += pnl_inr
                    trades.append({
                        "id": trade_id,
                        "direction": "Short" if is_credit else "Long",
                        "entry_date": entry_date,
                        "exit_date": day,
                        "entry_price": entry_price,
                        "exit_price": price,
                        "pnl": pnl_inr,
                        "pnl_pct": pnl_pct,
                        "strike": strike,
                        "option_type": option_type,
                        "expiry": str(row["expiry"]),
                        "exit_reason": reason,
                        "oi_entry": int(df.iloc[entry_idx].get("oi") or 0),
                        "oi_exit": int(row.get("oi") or 0),
                    })
                    trade_id += 1
                    in_position = False
            else:
                if day_trades < max_trades_day and entry_signal.iloc[i]:
                    if daily_sl > 0 and day_pnl <= -daily_sl:
                        pass
                    elif daily_tp > 0 and day_pnl >= daily_tp:
                        pass
                    else:
                        in_position = True
                        entry_price = price
                        entry_date = day
                        entry_idx = i
                        day_trades += 1

            mark = equity
            if in_position:
                pnl_pts = (entry_price - price) if is_credit else (price - entry_price)
                mark = equity + pnl_pts * lot_size
            equity_curve.append({"date": day, "value": float(mark)})

        eq_series = pd.Series([p["value"] for p in equity_curve])
        peak = eq_series.cummax()
        dd = ((eq_series - peak) / peak * 100).fillna(0)
        for j, d in enumerate(dd):
            drawdown_curve.append({"date": equity_curve[j]["date"], "value": float(d)})

        total_return = ((equity - initial_equity) / initial_equity) * 100 if initial_equity else 0
        days = max(len(df), 1)
        years = max(days / 252.0, 0.01)
        cagr = (((equity / initial_equity) ** (1 / years)) - 1) * 100 if initial_equity else 0
        max_dd = float(dd.min()) if len(dd) else 0

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = (len(wins) / len(trades) * 100) if trades else 0
        avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losses])) if losses else 1
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        expectancy = np.mean([t["pnl"] for t in trades]) if trades else 0

        rets = eq_series.pct_change().fillna(0)
        sharpe = float((rets.mean() / rets.std()) * np.sqrt(252)) if rets.std() > 0 else 0
        downside = rets[rets < 0]
        sortino = float((rets.mean() / downside.std()) * np.sqrt(252)) if len(downside) and downside.std() > 0 else 0
        calmar = cagr / abs(max_dd) if max_dd < 0 else 0

        return {
            "total_return": float(total_return),
            "cagr": float(cagr),
            "sharpe": sharpe,
            "sortino": sortino,
            "calmar": float(calmar),
            "max_drawdown": float(max_dd),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "expectancy": float(expectancy),
            "equity_curve": equity_curve,
            "drawdown": drawdown_curve,
            "trades": trades,
            "total_trades": len(trades),
        }


def _parse_date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(str(val)[:10], "%d-%m-%Y").date()
        except ValueError:
            return None


def _threshold(value, unit: str) -> dict | None:
    if value is None or value == "" or float(value) <= 0:
        return None
    return {"value": float(value), "unit": (unit or "%").lower()}


def _hit_sl(cfg: dict | None, pnl_pct: float, pnl_inr: float, pnl_pts: float) -> bool:
    if not cfg:
        return False
    v, u = cfg["value"], cfg["unit"]
    if u in ("%", "pct", "percent"):
        return pnl_pct <= -v
    if u in ("₹", "inr", "rupee", "rupees"):
        return pnl_inr <= -v
    if u in ("pts", "points", "point"):
        return pnl_pts <= -v
    return pnl_pct <= -v


def _hit_tp(cfg: dict | None, pnl_pct: float, pnl_inr: float, pnl_pts: float) -> bool:
    if not cfg:
        return False
    v, u = cfg["value"], cfg["unit"]
    if u in ("%", "pct", "percent"):
        return pnl_pct >= v
    if u in ("₹", "inr", "rupee", "rupees"):
        return pnl_inr >= v
    if u in ("pts", "points", "point"):
        return pnl_pts >= v
    return pnl_pct >= v
