"""
Build a production instruction-tuning dataset for equity backtesting LLMs.

Sources:
  - training/data/strategies/*.json
  - Postgres strategies table (if DATABASE_URL available)

Output:
  - training/data/qa_pairs/strykex_backtest_train.jsonl
  - training/data/qa_pairs/strykex_backtest_eval.jsonl

Usage:
  cd training
  python scripts/prepare_production_dataset.py
  python scripts/prepare_production_dataset.py --from-db --limit 500
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import random
import sys
from typing import Any

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

SYSTEM_PROMPT = (
    "You are StrykeX, a professional quant research assistant for Indian equities (NSE/BSE). "
    "You design backtestable strategies, interpret Pine Script, explain risk metrics, and use "
    "institutional conventions: VectorBT simulation, daily OHLCV from Postgres, explicit stop-loss, "
    "position sizing, and realistic slippage."
)


def _format_entry(entry_rules: Any) -> str:
    if isinstance(entry_rules, dict):
        if "conditions" in entry_rules:
            parts = []
            for c in entry_rules.get("conditions") or []:
                if isinstance(c, dict):
                    parts.append(
                        f"{c.get('indicator', 'rule')}({c.get('period', '')}) "
                        f"{c.get('operator', '')} {c.get('value', '')}".strip()
                    )
                else:
                    parts.append(str(c))
            return "; ".join(parts) or json.dumps(entry_rules)
        return json.dumps(entry_rules)
    return str(entry_rules)


def _format_exit(exit_rules: Any) -> str:
    if isinstance(exit_rules, dict):
        return (
            f"Stop loss: {exit_rules.get('stop_loss', 'N/A')}%, "
            f"Target: {exit_rules.get('take_profit') or exit_rules.get('target', 'N/A')}%, "
            f"Time exit: {exit_rules.get('time_exit', 'N/A')}"
        )
    return str(exit_rules)


def pairs_from_strategy(data: dict) -> list[dict]:
    name = data.get("name") or data.get("slug") or "Strategy"
    hypothesis = data.get("hypothesis") or "Systematic rule-based edge on NSE/BSE daily bars."
    entry = data.get("entry_rules") or data.get("logic", {}).get("entry", {})
    exit_r = data.get("exit_rules") or data.get("logic", {}).get("exit", {})
    risk = data.get("risk_params") or {}
    bt = data.get("backtest_results") or {}

    samples = [
        {
            "instruction": f"Describe the hypothesis behind the {name} strategy for Indian equities.",
            "input": "",
            "output": hypothesis,
        },
        {
            "instruction": f"What are the entry rules for {name}?",
            "input": "",
            "output": _format_entry(entry),
        },
        {
            "instruction": f"What are the exit and risk rules for {name}?",
            "input": "",
            "output": _format_exit(exit_r) + (f" Risk params: {json.dumps(risk)}" if risk else ""),
        },
        {
            "instruction": "Convert this strategy idea into a VectorBT-compatible JSON spec with entry/exit conditions.",
            "input": f"Strategy: {name}. Hypothesis: {hypothesis}",
            "output": json.dumps(
                {
                    "name": name,
                    "instrument_type": "EQUITY",
                    "entry": entry if isinstance(entry, dict) else {"conditions": []},
                    "exit": exit_r if isinstance(exit_r, dict) else {},
                    "stop_loss": risk.get("stop_loss") or exit_r.get("stop_loss") if isinstance(exit_r, dict) else None,
                    "take_profit": risk.get("take_profit") or exit_r.get("take_profit") if isinstance(exit_r, dict) else None,
                },
                indent=2,
            ),
        },
    ]

    if bt:
        samples.append(
            {
                "instruction": f"Summarize backtest results for {name} on {bt.get('symbol', 'NIFTY')}.",
                "input": "",
                "output": (
                    f"Total return: {bt.get('total_return', 'N/A')}%, "
                    f"Sharpe: {bt.get('sharpe', 'N/A')}, Max drawdown: {bt.get('max_drawdown', 'N/A')}%, "
                    f"Win rate: {bt.get('win_rate', 'N/A')}%, Trades: {bt.get('total_trades', 'N/A')}."
                ),
            }
        )

    # Professional backtest Q&A templates
    samples.extend(
        [
            {
                "instruction": "How should I backtest this on StrykeX using Postgres OHLCV?",
                "input": name,
                "output": (
                    "Use POST /api/backtest with strategy_spec JSON, symbol (e.g. NIFTY), period (1y/2y/5y), "
                    "interval 1d. Ensure OHLCV is ingested via ingest_all_nse.py. "
                    "Review Sharpe, max drawdown, profit factor, and monthly return stability before deployment."
                ),
            },
            {
                "instruction": "Write a Pine Script v5 strategy skeleton for this ruleset.",
                "input": f"Entry: {_format_entry(entry)} | Exit: {_format_exit(exit_r)}",
                "output": (
                    "//@version=5\nstrategy(\"" + name + "\", overlay=true)\n"
                    "// Map entry/exit rules to ta.rsi / ta.ema / ta.crossover\n"
                    "if entryCondition\n    strategy.entry(\"Long\", strategy.long)\n"
                    "if exitCondition\n    strategy.close(\"Long\")"
                ),
            },
        ]
    )

    for s in samples:
        s["system"] = SYSTEM_PROMPT
    return samples


def load_json_strategies(base_dir: str) -> list[dict]:
    files = glob.glob(os.path.join(base_dir, "**/*.json"), recursive=True)
    out = []
    for path in files:
        if "_schema" in path or "auto_generated" in path and random.random() > 0.3:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


async def load_db_strategies(limit: int) -> list[dict]:
    try:
        from sqlalchemy import text
        from app.db.session import async_session, is_db_available
    except Exception:
        return []

    if not is_db_available():
        return []

    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT name, slug, hypothesis, entry_rules, exit_rules, risk_params, backtest_results
                    FROM strategies
                    WHERE category NOT IN ('Options', 'Indicator Based', 'Fundamental')
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
        ).mappings().all()
        return [dict(r) for r in rows]


def to_chat_format(row: dict) -> dict:
    """Alpaca / ShareGPT style for TRL SFTTrainer."""
    user = row["instruction"]
    if row.get("input"):
        user = f"{user}\n\nContext:\n{row['input']}"
    return {
        "messages": [
            {"role": "system", "content": row.get("system", SYSTEM_PROMPT)},
            {"role": "user", "content": user},
            {"role": "assistant", "content": row["output"]},
        ]
    }


async def main(args: argparse.Namespace) -> None:
    strategies_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/strategies"))
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/qa_pairs"))
    os.makedirs(out_dir, exist_ok=True)

    strategies = load_json_strategies(strategies_dir)
    if args.from_db:
        strategies.extend(await load_db_strategies(args.limit))

    all_pairs: list[dict] = []
    for s in strategies:
        all_pairs.extend(pairs_from_strategy(s))

    random.shuffle(all_pairs)
    split = int(len(all_pairs) * (1 - args.eval_ratio))
    train_rows = all_pairs[:split]
    eval_rows = all_pairs[split:]

    train_path = os.path.join(out_dir, "strykex_backtest_train.jsonl")
    eval_path = os.path.join(out_dir, "strykex_backtest_eval.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for row in train_rows:
            f.write(json.dumps(to_chat_format(row), ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as f:
        for row in eval_rows:
            f.write(json.dumps(to_chat_format(row), ensure_ascii=False) + "\n")

    print(f"Strategies loaded: {len(strategies)}")
    print(f"Training samples: {len(train_rows)} -> {train_path}")
    print(f"Eval samples: {len(eval_rows)} -> {eval_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-db", action="store_true", help="Include Postgres strategies")
    parser.add_argument("--limit", type=int, default=200, help="Max DB strategies")
    parser.add_argument("--eval-ratio", type=float, default=0.08, help="Holdout fraction")
    asyncio.run(main(parser.parse_args()))
