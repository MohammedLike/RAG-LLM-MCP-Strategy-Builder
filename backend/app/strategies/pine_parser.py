"""Pine Script → strategy_spec JSON (heuristic parser for common patterns)."""

from __future__ import annotations

import re
from typing import Any

from ..backtest.indicators import IndicatorManager
from .compiler import parse_condition_str


def _cond(indicator: str, period: int, operator: str, value: Any) -> dict:
    return {
        "indicator": IndicatorManager.normalize_name(indicator),
        "params": {"timeperiod": period},
        "operator": operator,
        "value": value,
    }


def _crossover(fast_ind: str, fast_p: int, slow_ind: str, slow_p: int) -> dict:
    return _cond(
        fast_ind,
        fast_p,
        "crosses_above",
        {"indicator": IndicatorManager.normalize_name(slow_ind), "params": {"timeperiod": slow_p}},
    )


def _crossunder(fast_ind: str, fast_p: int, slow_ind: str, slow_p: int) -> dict:
    return _cond(
        fast_ind,
        fast_p,
        "crosses_below",
        {"indicator": IndicatorManager.normalize_name(slow_ind), "params": {"timeperiod": slow_p}},
    )


def parse_pine_script(source: str) -> dict[str, Any]:
    """Parse Pine Script into a strategy_spec compatible with BacktestEngine."""
    text = source.strip()
    if not text:
        return {"error": "Empty Pine Script"}

    lower = text.lower()
    warnings: list[str] = []

    stop_loss = 2.0
    take_profit = 5.0
    sl_match = re.search(r"stop\s*loss\s*=\s*([\d.]+)", lower)
    if sl_match:
        stop_loss = float(sl_match.group(1))
    tp_match = re.search(r"take\s*profit\s*=\s*([\d.]+)", lower)
    if tp_match:
        take_profit = float(tp_match.group(1))

    entry_conditions: list[dict] = []
    exit_conditions: list[dict] = []

    rsi_match = re.search(r"ta\.rsi\s*\([^,]+,\s*(\d+)\)", text, re.I)
    rsi_period = int(rsi_match.group(1)) if rsi_match else 14

    if re.search(r"ta\.crossover\s*\(\s*rsi", lower) or "rsi crosses above" in lower:
        thresh = 30
        t = re.search(r"rsi[^0-9]*(\d+)", lower)
        if t:
            thresh = int(t.group(1))
        entry_conditions.append(_cond("RSI", rsi_period, "crosses_above", thresh))
    elif re.search(r"rsi\s*[<>]=?\s*(\d+)", lower):
        m = re.search(r"rsi\s*([<>]=?)\s*(\d+)", lower)
        if m:
            op = ">" if ">" in m.group(1) else "<"
            entry_conditions.append(_cond("RSI", rsi_period, op, int(m.group(2))))

    sma_fast = re.search(r"ta\.sma\s*\([^,]+,\s*(\d+)\)", text, re.I)
    sma_slow = re.findall(r"ta\.sma\s*\([^,]+,\s*(\d+)\)", text, re.I)
    ema_fast = re.search(r"ta\.ema\s*\([^,]+,\s*(\d+)\)", text, re.I)
    ema_periods = [int(x) for x in re.findall(r"ta\.ema\s*\([^,]+,\s*(\d+)\)", text, re.I)]

    if re.search(r"ta\.crossover\s*\(\s*(?:fast|ema|sma)", lower) or "golden cross" in lower:
        if len(ema_periods) >= 2:
            entry_conditions.append(_crossover("EMA", ema_periods[0], "EMA", ema_periods[1]))
        elif len(sma_slow) >= 2:
            entry_conditions.append(_crossover("SMA", int(sma_slow[0]), "SMA", int(sma_slow[1])))
    elif sma_fast and len(sma_slow) >= 2:
        entry_conditions.append(_crossover("SMA", int(sma_slow[0]), "SMA", int(sma_slow[1])))

    if re.search(r"ta\.crossunder", lower) or "death cross" in lower:
        if len(ema_periods) >= 2:
            exit_conditions.append(_crossunder("EMA", ema_periods[0], "EMA", ema_periods[1]))
        elif len(sma_slow) >= 2:
            exit_conditions.append(_crossunder("SMA", int(sma_slow[0]), "SMA", int(sma_slow[1])))

    if re.search(r"ta\.crossover\s*\(\s*rsi", lower) and rsi_match:
        exit_conditions.append(_cond("RSI", rsi_period, "crosses_above", 70))

    long_comment = re.search(r"//\s*long:\s*(.+)$", text, re.I | re.M)
    if long_comment and not entry_conditions:
        try:
            entry_conditions.append(parse_condition_str(long_comment.group(1).strip()))
        except Exception:
            warnings.append("Could not parse // long: comment")

    if not entry_conditions:
        if "strategy(" in lower:
            warnings.append("Pine strategy() detected but entry logic not auto-parsed — add RSI/SMA/EMA patterns or use AI interpret.")
        return {
            "error": "Could not extract entry conditions from Pine Script. Use common ta.rsi / ta.sma / ta.crossover patterns.",
            "warnings": warnings,
            "raw_preview": text[:500],
        }

    spec = {
        "instrument_type": "EQUITY",
        "entry": {"conditions": entry_conditions, "logical_operator": "AND"},
        "exit": {"conditions": exit_conditions, "logical_operator": "OR"} if exit_conditions else {},
        "stop_loss": stop_loss,
        "take_profit": take_profit,
    }

    return {
        "strategy_spec": spec,
        "source": "pine_heuristic",
        "warnings": warnings,
        "summary": _summarize_spec(spec),
    }


def _summarize_spec(spec: dict) -> str:
    entry = spec.get("entry", {}).get("conditions", [])
    parts = []
    for c in entry[:3]:
        ind = c.get("indicator", "?")
        op = c.get("operator", "?")
        val = c.get("value", "")
        parts.append(f"{ind} {op} {val}")
    sl = spec.get("stop_loss")
    tp = spec.get("take_profit")
    risk = f"SL {sl}% / TP {tp}%" if sl or tp else ""
    return "Entry: " + "; ".join(parts) + (f" | {risk}" if risk else "")
