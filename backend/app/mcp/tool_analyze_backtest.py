"""AI analysis of backtest results — rule-based insights + optional LLM summary."""

from __future__ import annotations

from typing import Any


def analyze_backtest_result(result: dict) -> dict[str, Any]:
    if result.get("error"):
        return {"error": result["error"], "suggestions": []}

    total_return = float(result.get("total_return") or 0)
    sharpe = float(result.get("sharpe") or 0)
    max_dd = float(result.get("max_drawdown") or 0)
    win_rate = float(result.get("win_rate") or 0)
    trades = len(result.get("trades") or [])
    profit_factor = float(result.get("profit_factor") or 0)

    suggestions: list[dict] = []
    summary_parts = []

    if trades < 10:
        suggestions.append({
            "type": "data",
            "severity": "warning",
            "message": f"Only {trades} trades — extend period or relax entry rules for statistical significance.",
        })
        summary_parts.append("Low trade count.")

    if sharpe < 0.5 and total_return > 0:
        suggestions.append({
            "type": "risk",
            "severity": "info",
            "message": "Positive return but Sharpe below 0.5 — returns may be volatile relative to risk.",
            "action": "Tighten stop loss or add trend filter (e.g. price above 200 SMA).",
        })

    if max_dd < -25:
        suggestions.append({
            "type": "risk",
            "severity": "critical",
            "message": f"Max drawdown {max_dd:.1f}% is high for equity strategies.",
            "action": "Reduce position size or add exit rules; try stop_loss grid optimization.",
        })
        summary_parts.append("High drawdown.")

    if win_rate < 40 and profit_factor > 1.2:
        suggestions.append({
            "type": "style",
            "severity": "info",
            "message": "Low win rate but positive profit factor — typical of trend-following; ensure SL/TP ratios are intentional.",
        })

    if win_rate > 60 and total_return < 5:
        suggestions.append({
            "type": "params",
            "severity": "info",
            "message": "High win rate but modest return — winners may be too small.",
            "action": "Increase take_profit or trail winners.",
        })

    if sharpe >= 1.0 and max_dd > -15:
        suggestions.append({
            "type": "approval",
            "severity": "success",
            "message": "Solid risk-adjusted profile — candidate for paper trading validation.",
        })
        summary_parts.append("Strong risk-adjusted metrics.")

    param_hints = {}
    spec = result.get("strategy_spec") or {}
    if spec.get("stop_loss") is not None:
        sl = float(spec["stop_loss"])
        if max_dd < -20:
            param_hints["stop_loss"] = [max(0.5, sl - 1), sl, sl + 1]
        else:
            param_hints["stop_loss"] = [sl, sl + 1, sl + 2]
    if spec.get("take_profit") is not None:
        tp = float(spec["take_profit"])
        param_hints["take_profit"] = [tp, tp + 2, tp + 5]

    narrative = (
        f"Backtest on {result.get('symbol', '?')} ({result.get('period', '?')}): "
        f"return {total_return:+.1f}%, Sharpe {sharpe:.2f}, max DD {max_dd:.1f}%, "
        f"win rate {win_rate:.0f}%, {trades} trades. "
        + (" ".join(summary_parts) if summary_parts else "Review suggestions below.")
    )

    return {
        "narrative": narrative,
        "metrics": {
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "trades": trades,
        },
        "suggestions": suggestions,
        "recommended_param_grid": param_hints,
        "approval_status": "pending",
    }
