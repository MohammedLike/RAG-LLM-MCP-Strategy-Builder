"""AI-powered Pine Script generation and strategy spec for the Quant Pipeline."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

import ollama

from ..config import settings
from ..nl_parser import nl_parser
from .pine_parser import parse_pine_script

_client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

PINE_BUILDER_SYSTEM = """You are StrykeX Pine Quant Builder AI for Indian markets (NSE/BSE).

The user describes a trading strategy. You must output ONLY a single JSON object (no markdown outside the JSON) with this exact shape:

{
  "pine_script": "//@version=5\\nstrategy(\\"My Strategy\\", overlay=true)\\n... full Pine Script v5 ...",
  "strategy_spec": {
    "instrument_type": "EQUITY",
    "entry": {
      "conditions": [
        {"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "crosses_below", "value": 30}
      ],
      "logical_operator": "AND"
    },
    "exit": {
      "conditions": [
        {"indicator": "RSI", "params": {"timeperiod": 14}, "operator": "crosses_above", "value": 70}
      ],
      "logical_operator": "OR"
    },
    "stop_loss": 2.0,
    "take_profit": 5.0
  },
  "explanation": "One sentence describing the strategy.",
  "symbol": "NIFTY",
  "period": "2y"
}

Rules:
- pine_script must be valid TradingView Pine Script v5 with strategy() declaration, ta.rsi/ta.sma/ta.ema/ta.crossover where possible, and clear long entry/exit logic.
- strategy_spec must mirror the Pine logic using supported indicators: RSI, SMA, EMA, MACD, ATR, ADX, CCI, STOCH, BBANDS, CLOSE, OPEN, HIGH, LOW, VOLUME.
- Supported operators: crosses_above, crosses_below, >, <, >=, <=, ==.
- Default symbol NIFTY unless user specifies BANKNIFTY, RELIANCE, etc.
- period: 1y, 2y, or 5y.
- stop_loss and take_profit as percentages (e.g. 2.0 = 2%).
- entry.conditions must not be empty.
"""

PINE_CHAT_SYSTEM = """You are StrykeX Pine Quant Builder Assistant embedded in a quant backtesting platform.

You help users design Pine Script strategies for Indian equities/indices. When they ask you to create or backtest a strategy:
1. Explain briefly what you will build.
2. Tell them to click "Generate Pine" or "Generate & Backtest" for full Pine code and a database backtest.

Supported backtest data: Postgres OHLCV (daily NIFTY/BANKNIFTY/stocks). Keep answers concise and practical.
"""


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if block:
        try:
            return json.loads(block.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


def _normalize_spec(spec: dict) -> dict:
    spec = dict(spec or {})
    spec.setdefault("instrument_type", "EQUITY")
    entry = spec.get("entry") or {}
    if not entry.get("conditions"):
        raise ValueError("strategy_spec.entry.conditions is empty")
    spec.setdefault("stop_loss", 2.0)
    spec.setdefault("take_profit", 5.0)
    return spec


def _fallback_from_nl(prompt: str, symbol: str, period: str) -> dict[str, Any]:
    parsed = nl_parser.parse(prompt)
    if parsed and parsed.get("strategy_spec"):
        spec = _normalize_spec(parsed["strategy_spec"])
        pine_lines = [
            "//@version=5",
            f'strategy("StrykeX {symbol}", overlay=true, default_qty_type=strategy.percent_of_equity, default_qty_value=100)',
            f"// Generated fallback from: {prompt[:120]}",
            "// Auto-transpile limited — edit in TradingView as needed",
        ]
        for i, c in enumerate(spec.get("entry", {}).get("conditions", [])[:2]):
            ind = c.get("indicator", "RSI")
            p = (c.get("params") or {}).get("timeperiod", 14)
            op = c.get("operator", ">")
            val = c.get("value", 30)
            pine_lines.append(f"// Entry {i + 1}: {ind}({p}) {op} {val}")
        pine_lines.append("longCondition = true  // placeholder — refine in TradingView")
        pine_lines.append("if longCondition\n    strategy.entry(\"Long\", strategy.long)")
        return {
            "pine_script": "\n".join(pine_lines),
            "strategy_spec": spec,
            "explanation": "Built from rule-based parser (LLM unavailable).",
            "symbol": parsed.get("symbol") or symbol,
            "period": parsed.get("period") or period,
            "source": "nl_fallback",
        }
    raise ValueError("Could not build strategy from prompt. Try clearer RSI/SMA/EMA rules.")


async def generate_pine_strategy(
    prompt: str,
    symbol: str = "NIFTY",
    period: str = "2y",
    interval: str = "1d",
) -> dict[str, Any]:
    user_msg = (
        f"Symbol: {symbol}\nPeriod: {period}\nInterval: {interval}\n\n"
        f"Strategy request:\n{prompt}"
    )
    try:
        response = await _client.chat(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": PINE_BUILDER_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            options={"temperature": 0.15},
        )
        content = response.get("message", {}).get("content", "")
        data = _extract_json(content)
        if not data or not data.get("strategy_spec"):
            raise ValueError("LLM did not return valid JSON with strategy_spec")

        spec = _normalize_spec(data["strategy_spec"])
        pine_script = (data.get("pine_script") or "").strip()
        if not pine_script:
            reparsed = parse_pine_script(f"// fallback\n{prompt}")
            pine_script = reparsed.get("raw_preview") or f"//@version=5\n// {prompt}"

        return {
            "pine_script": pine_script,
            "strategy_spec": spec,
            "explanation": data.get("explanation", "AI-generated strategy"),
            "symbol": data.get("symbol") or symbol,
            "period": data.get("period") or period,
            "interval": interval,
            "source": "ollama",
            "model": settings.LLM_MODEL_NAME,
        }
    except Exception as exc:
        print(f"Pine AI LLM error: {exc}")
        fallback = _fallback_from_nl(prompt, symbol, period)
        fallback["interval"] = interval
        fallback["llm_error"] = str(exc)
        return fallback


async def chat_pine_assistant(
    message: str,
    history: list[dict] | None = None,
    symbol: str = "NIFTY",
) -> dict[str, Any]:
    messages = [{"role": "system", "content": f"{PINE_CHAT_SYSTEM}\nCurrent symbol: {symbol}"}]
    for h in history or []:
        role = h.get("role", "user")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    try:
        response = await _client.chat(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            options={"temperature": 0.3},
        )
        reply = response.get("message", {}).get("content", "").strip()
        return {"reply": reply, "model": settings.LLM_MODEL_NAME}
    except Exception as exc:
        return {
            "reply": (
                f"I couldn't reach the AI model ({exc}). "
                "Use **Generate Pine** for rule-based strategy building, or start Ollama with `{settings.LLM_MODEL_NAME}`."
            ),
            "error": str(exc),
        }


def save_generated_pine(pine_script: str, label: str = "ai") -> str:
    """Deprecated — pipeline routes persist via db.pine_store.save_pine_script."""
    return f"{label}_{uuid.uuid4().hex[:8]}"


async def interpret_with_ai(
    content: str,
    source_type: str,
    symbol: str,
    period: str,
    interval: str,
) -> dict[str, Any]:
    """Interpret pine/text; fall back to AI generation for natural language."""
    if source_type == "pine":
        parsed = parse_pine_script(content)
        if parsed.get("strategy_spec"):
            return {
                **parsed,
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "source": parsed.get("source", "pine"),
            }
        ai = await generate_pine_strategy(
            f"Convert this Pine Script to backtest rules:\n{content[:3000]}",
            symbol=symbol,
            period=period,
            interval=interval,
        )
        ai["source"] = "ai_from_pine"
        ai["warnings"] = [parsed.get("error", "Heuristic pine parse failed")] if parsed.get("error") else []
        return ai

    nl = nl_parser.parse(content)
    if nl and nl.get("strategy_spec"):
        return {
            "strategy_spec": nl["strategy_spec"],
            "symbol": nl.get("symbol") or symbol,
            "period": nl.get("period") or period,
            "interval": interval,
            "source": "nl_parser",
            "summary": content[:200],
            "warnings": [],
        }

    return await generate_pine_strategy(content, symbol=symbol, period=period, interval=interval)
