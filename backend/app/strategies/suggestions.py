"""Build pre-built strategy suggestion catalog from the strategies table."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from app.backtest.indicator_db import INDICATORS_DB
from app.backtest.indicators import IndicatorManager
from app.strategies.compiler import compile_db_strategy, parse_condition_str

INDICATOR_FALLBACK_NAMES: dict[str, str] = {
    "PREV_N": "Previous N",
    "OPENING_RANGE": "Opening Range",
    "DONCHIAN_CHANNEL": "Donchian Channel",
    "ICHIMOKU": "Ichimoku Cloud",
    "KELTNER": "Keltner Channel",
    "VORTEX": "Vortex Indicator",
    "TII": "Trend Intensity Index",
    "PLUS_DI": "+DI",
    "MINUS_DI": "-DI",
    "BBANDS": "Bollinger Bands",
    "STOCH": "Stochastic",
    "WILLR": "Williams %R",
    "MACD": "MACD",
    "OBV": "On Balance Volume",
    "MFI": "Money Flow Index",
    "ATR": "Average True Range",
    "ADX": "Average Directional Index",
    "CCI": "Commodity Channel Index",
    "ROC": "Rate of Change",
    "VWAP": "VWAP",
    "CLOSE": "Close Price",
    "HIGH": "High Price",
    "VOLUME": "Volume",
    "MIDPOINT": "Midpoint",
    "UNKNOWN": "Other",
}

CATEGORY_SLUG_MAP = {
    "Overlap Studies": "overlap studies",
    "Momentum Indicators": "momentum indicators",
    "Oscillators": "oscillators",
    "Volume Indicators": "volume indicators",
    "Volatility Indicators": "volatility indicators",
    "Price Transform": "price transform",
    "Cycle Indicators": "cycle indicators",
    "Pattern Recognition": "pattern recognition",
    "Statistic Functions": "statistic functions",
    "Math Operators": "math operators",
    "Math Transform": "math transform",
    "General": "general",
}


def _normalize_json(value: Any) -> dict:
    if not value:
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _format_structured_condition(cond: dict) -> str:
    indicator = cond.get("indicator", "CLOSE")
    params = cond.get("params") or {}
    period = params.get("timeperiod", params.get("period", 14))
    operator = (cond.get("operator") or "==").replace("_", " ")
    value = cond.get("value")
    if isinstance(value, dict) and value.get("indicator"):
        rhs = f"{value['indicator']}({value.get('params', {}).get('timeperiod', 14)})"
    else:
        rhs = str(value)
    return f"{indicator}({period}) {operator} {rhs}"


def format_condition_display(entry_rules: dict, backtest_spec: dict | None = None) -> str:
    if entry_rules.get("condition"):
        return str(entry_rules["condition"]).strip()
    entry = (backtest_spec or {}).get("entry") or {}
    conditions = entry.get("conditions") or []
    if conditions:
        return _format_structured_condition(conditions[0])
    if entry_rules.get("indicator"):
        return _format_structured_condition(entry_rules)
    return ""


def extract_primary_indicator(entry_rules: dict, name: str = "") -> str:
    if entry_rules.get("condition"):
        parsed = parse_condition_str(entry_rules["condition"])
        indicator = parsed.get("indicator")
        if indicator and indicator != "CLOSE":
            return IndicatorManager.normalize_name(indicator)

    for cond in entry_rules.get("conditions") or []:
        if cond.get("indicator"):
            return IndicatorManager.normalize_name(cond["indicator"])

    if entry_rules.get("indicator"):
        return IndicatorManager.normalize_name(entry_rules["indicator"])

    if entry_rules.get("condition"):
        match = re.search(r"([A-Za-z][A-Za-z0-9 %_\-\./]+?)\s*\(", entry_rules["condition"])
        if match:
            raw = match.group(1).strip().upper().replace(" ", "_")
            return IndicatorManager.normalize_name(raw)

    name_upper = name.upper()
    for key in sorted(INDICATORS_DB.keys(), key=len, reverse=True):
        if key in name_upper.replace(" ", "_"):
            return key

    return "UNKNOWN"


def infer_direction(name: str, condition_text: str, entry_rules: dict, slug: str = "") -> str:
    blob = f"{name} {condition_text} {slug}".lower()
    bearish_markers = (
        "bearish", "bear_", "bear ", "death cross", "downtrend", "downside",
        "lower low", "breakdown", "weak", "short-term", "short term",
    )
    bullish_markers = (
        "bullish", "bull_", "bull ", "golden cross", "uptrend", "upside",
        "breakout", "strength", "recovery", "accumulation", "long-term", "long term",
    )
    if any(m in blob for m in bearish_markers):
        return "bearish"
    if any(m in blob for m in bullish_markers):
        return "bullish"

    cond = (entry_rules.get("condition") or condition_text or "").lower()
    if any(op in cond for op in ("crosses above", "crosses_above", "higher than", ">")):
        return "bullish"
    if any(op in cond for op in ("crosses below", "crosses_below", "lower than", "<")):
        return "bearish"
    return "neutral"


def infer_style_tag(category: str, entry_rules: dict, name: str) -> str:
    timeframe = str(entry_rules.get("timeframe") or "").lower()
    name_lower = name.lower()
    if any(t in timeframe for t in ("1min", "5min", "15min", "30min", "1h")):
        return "Intraday Momentum"
    if "scalp" in name_lower:
        return "Scalping"
    if category in ("Trend Following", "Trend Strength", "Momentum"):
        return "Trend Following"
    if category in ("Mean Reversion", "Pullback"):
        return "Scalping"
    if category in ("Breakout", "Volatility"):
        return "Longterm"
    if category == "Equity":
        return "Equity"
    if category == "Indicator Based":
        return "Indicator Based"
    return category or "General"


def _indicator_meta(indicator_id: str) -> dict:
    db_entry = INDICATORS_DB.get(indicator_id)
    if db_entry:
        return {
            "id": indicator_id,
            "name": db_entry["name"],
            "long_name": db_entry["long_name"],
            "category": db_entry["category"],
            "description": db_entry.get("description", ""),
            "params": db_entry.get("params", {}),
        }
    long_name = INDICATOR_FALLBACK_NAMES.get(indicator_id, indicator_id.replace("_", " ").title())
    return {
        "id": indicator_id,
        "name": indicator_id,
        "long_name": long_name,
        "category": "General",
        "description": f"Pre-built setups using {long_name}.",
        "params": {},
    }


def build_prebuilt_catalog(rows: list) -> dict:
    suggestions_by_indicator: dict[str, list] = defaultdict(list)
    indicator_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        name = row[0]
        slug = row[1]
        category = row[2] or "General"
        hypothesis = row[3] or ""
        entry_rules = _normalize_json(row[4])
        exit_rules = _normalize_json(row[5])
        risk_params = _normalize_json(row[6])

        db_strat = {
            "name": name,
            "slug": slug,
            "category": category,
            "hypothesis": hypothesis,
            "entry_rules": entry_rules,
            "exit_rules": exit_rules,
            "risk_params": risk_params,
        }

        try:
            backtest_spec = compile_db_strategy(db_strat)
        except Exception:
            backtest_spec = {}

        condition_text = format_condition_display(entry_rules, backtest_spec)
        primary = extract_primary_indicator(entry_rules, name)
        direction = infer_direction(name, condition_text, entry_rules, slug)
        style_tag = infer_style_tag(category, entry_rules, name)

        suggestion = {
            "slug": slug,
            "name": name,
            "category": category,
            "hypothesis": hypothesis,
            "condition_text": condition_text or name,
            "direction": direction,
            "style_tag": style_tag,
            "timeframe": entry_rules.get("timeframe"),
            "indicator": primary,
            "backtest_spec": backtest_spec,
            "entry_rules": entry_rules,
            "exit_rules": exit_rules,
        }
        suggestions_by_indicator[primary].append(suggestion)
        indicator_counts[primary] += 1

    indicators = []
    for indicator_id, count in sorted(indicator_counts.items(), key=lambda x: (-x[1], x[0])):
        meta = _indicator_meta(indicator_id)
        meta["count"] = count
        meta["letter"] = meta["name"][:1].upper()
        meta["category_slug"] = CATEGORY_SLUG_MAP.get(meta["category"], meta["category"].lower())
        indicators.append(meta)

    category_filters = ["All"]
    seen = set()
    for ind in indicators:
        slug = ind["category_slug"]
        if slug not in seen:
            category_filters.append(ind["category"])
            seen.add(slug)

    alphabet = sorted({ind["letter"] for ind in indicators if ind["letter"].isalpha()})

    return {
        "total_strategies": sum(indicator_counts.values()),
        "total_indicators": len(indicators),
        "categories": category_filters,
        "alphabet": alphabet,
        "indicators": indicators,
        "suggestions_by_indicator": dict(suggestions_by_indicator),
    }


def filter_catalog(
    catalog: dict,
    *,
    q: str | None = None,
    indicator: str | None = None,
    direction: str | None = None,
    category: str | None = None,
    letter: str | None = None,
) -> dict:
    """Return a filtered view of the catalog (client can also filter locally)."""
    indicators = catalog["indicators"]
    suggestions_map = catalog["suggestions_by_indicator"]

    if letter:
        indicators = [i for i in indicators if i["letter"] == letter.upper()]

    if category and category.lower() != "all":
        indicators = [
            i for i in indicators
            if i["category"].lower() == category.lower() or i["category_slug"] == category.lower()
        ]

    if indicator:
        indicator = IndicatorManager.normalize_name(indicator)
        indicators = [i for i in indicators if i["id"] == indicator]
        suggestions_map = {indicator: suggestions_map.get(indicator, [])}

    filtered_suggestions: dict[str, list] = {}
    q_lower = q.lower().strip() if q else None
    dir_filter = direction.lower() if direction and direction.lower() != "all" else None

    for ind in indicators:
        items = suggestions_map.get(ind["id"], [])
        filtered = []
        for item in items:
            if dir_filter and item["direction"] != dir_filter:
                continue
            if q_lower:
                haystack = " ".join([
                    item["name"],
                    item.get("condition_text") or "",
                    item.get("hypothesis") or "",
                    item.get("style_tag") or "",
                ]).lower()
                if q_lower not in haystack:
                    continue
            filtered.append(item)
        if filtered:
            filtered_suggestions[ind["id"]] = filtered

    indicators = [i for i in indicators if i["id"] in filtered_suggestions]

    return {
        **catalog,
        "indicators": indicators,
        "suggestions_by_indicator": filtered_suggestions,
        "total_indicators": len(indicators),
        "total_strategies": sum(len(v) for v in filtered_suggestions.values()),
    }
