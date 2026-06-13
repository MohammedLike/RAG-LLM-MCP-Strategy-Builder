"""Live automated strategy runner — Pine → signals → paper/live execution."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from ..backtest.engine import BacktestEngine
from ..config import settings
from ..market.provider_yfinance import YFinanceProvider
from ..strategies.pine_ai import interpret_with_ai
from .paper_broker import broker_for_mode
from . import store

_provider = YFinanceProvider()
_engine = BacktestEngine()

LOOKBACK_DAYS = {
    "1m": 14,
    "5m": 30,
    "15m": 60,
    "1h": 120,
    "1d": 400,
}


async def convert_pine_to_strategy(
    pine_script: str,
    symbol: str = "NIFTY",
    period: str = "2y",
    interval: str = "1d",
    use_ai: bool = True,
) -> dict[str, Any]:
    """Convert TradingView Pine Script to executable strategy_spec + optional backtest preview."""
    if not pine_script.strip():
        return {"error": "Empty Pine Script"}

    if use_ai:
        result = await interpret_with_ai(pine_script, "pine", symbol, period, interval)
    else:
        from ..strategies.pine_parser import parse_pine_script
        result = parse_pine_script(pine_script)
        if result.get("strategy_spec"):
            result.setdefault("symbol", symbol)
            result.setdefault("period", period)
            result.setdefault("interval", interval)

    if result.get("error") and not result.get("strategy_spec"):
        return result

    return {
        "pine_script": result.get("pine_script") or pine_script,
        "strategy_spec": result["strategy_spec"],
        "symbol": result.get("symbol") or symbol,
        "period": result.get("period") or period,
        "interval": interval,
        "source": result.get("source", "pine"),
        "summary": result.get("summary") or result.get("explanation", ""),
        "warnings": result.get("warnings", []),
        "ready_for_live": True,
    }


async def _fetch_bars(symbol: str, interval: str) -> pd.DataFrame:
    days = LOOKBACK_DAYS.get(interval, 400)
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    df = await _provider.get_ohlcv(symbol, interval, start, end)
    if df.empty:
        from ..market.parquet_store import read_ohlcv
        df = read_ohlcv(symbol, interval, start, end)
    return df


def _latest_signals(df: pd.DataFrame, strategy_spec: dict) -> dict[str, Any]:
    if df.empty or len(df) < 2:
        return {"error": "Not enough OHLCV bars for signal evaluation"}

    work = df.copy()
    if "time" in work.columns:
        work = work.set_index("time")

    entries = _engine.evaluate_rules(work, strategy_spec.get("entry", {}))
    exits = _engine.evaluate_rules(work, strategy_spec.get("exit", {}))

    last_idx = work.index[-1]
    prev_idx = work.index[-2]
    last_close = float(work["close"].iloc[-1])

    entry_now = bool(entries.iloc[-1]) if len(entries) else False
    entry_prev = bool(entries.iloc[-2]) if len(entries) > 1 else False
    exit_now = bool(exits.iloc[-1]) if len(exits) else False
    exit_prev = bool(exits.iloc[-2]) if len(exits) > 1 else False

    entry_trigger = entry_now and not entry_prev
    exit_trigger = exit_now and not exit_prev

    return {
        "bar_time": str(last_idx),
        "price": last_close,
        "entry_signal": entry_now,
        "exit_signal": exit_now,
        "entry_trigger": entry_trigger,
        "exit_trigger": exit_trigger,
        "prev_bar": str(prev_idx),
    }


async def deploy_strategy(
    *,
    name: str,
    symbol: str,
    interval: str,
    strategy_spec: dict,
    pine_script: str = "",
    mode: str = "paper",
    capital: float = 100_000.0,
    quantity: int = 1,
) -> dict[str, Any]:
    strategy_id = f"live_{uuid.uuid4().hex[:10]}"
    record = {
        "id": strategy_id,
        "name": name or f"Pine {symbol} {interval}",
        "symbol": symbol.upper(),
        "interval": interval,
        "strategy_spec": strategy_spec,
        "pine_script": pine_script,
        "mode": mode if mode in ("paper", "live") else "paper",
        "status": "active",
        "capital": capital,
        "cash": capital,
        "quantity": max(1, quantity),
        "position": {"side": "flat", "qty": 0, "avg_price": 0.0},
        "orders": [],
        "ticks": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_tick_at": None,
        "last_signal": None,
    }
    store.upsert(strategy_id, record)
    return record


async def tick_strategy(strategy_id: str) -> dict[str, Any]:
    """Evaluate latest bar and execute paper/live orders if triggers fire."""
    strategy = store.get(strategy_id)
    if not strategy:
        return {"error": "Strategy not found"}
    if strategy.get("status") != "active":
        return {"error": "Strategy is stopped", "strategy_id": strategy_id}

    df = await _fetch_bars(strategy["symbol"], strategy["interval"])
    signals = _latest_signals(df, strategy["strategy_spec"])
    if signals.get("error"):
        return {"strategy_id": strategy_id, **signals}

    broker = broker_for_mode(strategy.get("mode", "paper"))
    orders_placed = []
    position = strategy.get("position") or {"side": "flat", "qty": 0}

    if signals["exit_trigger"] and position.get("side") == "long":
        o = broker.execute(
            strategy, "SELL", signals["price"], strategy.get("quantity", 1), "exit_signal"
        )
        orders_placed.append(o)
    elif signals["entry_trigger"] and position.get("side") == "flat":
        o = broker.execute(
            strategy, "BUY", signals["price"], strategy.get("quantity", 1), "entry_signal"
        )
        orders_placed.append(o)

    tick_log = {
        "at": datetime.utcnow().isoformat(),
        "signals": signals,
        "orders": orders_placed,
        "position_after": strategy.get("position"),
    }
    ticks = strategy.get("ticks") or []
    ticks.append(tick_log)
    strategy["ticks"] = ticks[-50:]
    strategy["last_tick_at"] = tick_log["at"]
    strategy["last_signal"] = signals
    store.upsert(strategy_id, strategy)

    return {
        "strategy_id": strategy_id,
        "signals": signals,
        "orders": orders_placed,
        "position": strategy.get("position"),
        "cash": strategy.get("cash"),
        "status": strategy.get("status"),
        "mode": strategy.get("mode"),
    }


def list_strategies() -> list[dict]:
    items = list(store.load_all().values())
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return [
        {
            "id": s["id"],
            "name": s.get("name"),
            "symbol": s.get("symbol"),
            "interval": s.get("interval"),
            "mode": s.get("mode"),
            "status": s.get("status"),
            "position": s.get("position"),
            "last_tick_at": s.get("last_tick_at"),
            "last_signal": s.get("last_signal"),
            "orders_count": len(s.get("orders") or []),
            "created_at": s.get("created_at"),
        }
        for s in items
    ]


def get_strategy_detail(strategy_id: str) -> dict | None:
    s = store.get(strategy_id)
    if not s:
        return None
    return {
        **s,
        "pine_script_preview": (s.get("pine_script") or "")[:500],
    }


def stop_strategy(strategy_id: str) -> dict:
    s = store.get(strategy_id)
    if not s:
        return {"error": "Strategy not found"}
    s["status"] = "stopped"
    s["stopped_at"] = datetime.utcnow().isoformat()
    store.upsert(strategy_id, s)
    return {"strategy_id": strategy_id, "status": "stopped"}


def start_strategy(strategy_id: str) -> dict:
    s = store.get(strategy_id)
    if not s:
        return {"error": "Strategy not found"}
    s["status"] = "active"
    store.upsert(strategy_id, s)
    return {"strategy_id": strategy_id, "status": "active"}
