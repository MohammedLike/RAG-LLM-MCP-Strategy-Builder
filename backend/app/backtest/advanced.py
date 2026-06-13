"""Advanced backtesting analytics — Monte Carlo, walk-forward, comparison."""

from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pandas as pd

from .engine import BacktestEngine
from .metrics import compute_monthly_returns_by_year


def run_monte_carlo(
    trades: list[dict],
    n_simulations: int = 1000,
    initial_capital: float = 100.0,
) -> dict[str, Any]:
    """Bootstrap trade returns to estimate outcome distribution."""
    if not trades:
        return {"error": "No trades to simulate"}

    returns = [float(t.get("pnl_pct", 0)) / 100.0 for t in trades]
    if len(returns) < 3:
        return {"error": "Need at least 3 trades for Monte Carlo"}

    n_trades = len(returns)
    rng = np.random.default_rng(42)
    paths = np.zeros((n_simulations, n_trades + 1))
    paths[:, 0] = initial_capital

    for sim in range(n_simulations):
        sampled = rng.choice(returns, size=n_trades, replace=True)
        equity = initial_capital
        for i, r in enumerate(sampled):
            equity *= 1 + r
            paths[sim, i + 1] = equity

    percentiles = [5, 25, 50, 75, 95]
    curve: list[dict] = []
    for step in range(n_trades + 1):
        vals = np.sort(paths[:, step])
        row: dict[str, Any] = {"step": step}
        for p in percentiles:
            row[f"p{p}"] = round(float(np.percentile(vals, p)), 2)
        curve.append(row)

    final = paths[:, -1]
    prob_profit = float((final > initial_capital).sum() / n_simulations * 100)

    return {
        "n_simulations": n_simulations,
        "n_trades": n_trades,
        "initial_capital": initial_capital,
        "prob_profit_pct": round(prob_profit, 2),
        "median_final": round(float(np.median(final)), 2),
        "p5_final": round(float(np.percentile(final, 5)), 2),
        "p95_final": round(float(np.percentile(final, 95)), 2),
        "mean_final": round(float(np.mean(final)), 2),
        "worst_case": round(float(np.min(final)), 2),
        "best_case": round(float(np.max(final)), 2),
        "curve": curve,
    }


def run_walk_forward(
    df: pd.DataFrame,
    strategy_spec: dict,
    n_splits: int = 5,
    train_ratio: float = 0.7,
) -> dict[str, Any]:
    """Rolling walk-forward validation across time windows."""
    if df.empty or len(df) < 60:
        return {"error": "Insufficient data for walk-forward"}

    engine = BacktestEngine()
    work = df.copy()
    if "time" in work.columns:
        work = work.sort_values("time").reset_index(drop=True)

    total = len(work)
    window = max(total // n_splits, 40)
    folds: list[dict] = []

    for i in range(n_splits):
        start = i * (window // 2)
        end = min(start + window, total)
        if end - start < 30:
            continue

        chunk = work.iloc[start:end].copy()
        split_idx = int(len(chunk) * train_ratio)
        train_df = chunk.iloc[:split_idx]
        test_df = chunk.iloc[split_idx:]

        if len(train_df) < 20 or len(test_df) < 10:
            continue

        try:
            in_sample = engine.run(train_df, copy.deepcopy(strategy_spec))
            out_sample = engine.run(test_df, copy.deepcopy(strategy_spec))
        except Exception as e:
            folds.append({"fold": i + 1, "error": str(e)})
            continue

        folds.append({
            "fold": i + 1,
            "train_bars": len(train_df),
            "test_bars": len(test_df),
            "train_start": str(train_df["time"].iloc[0])[:10] if "time" in train_df.columns else None,
            "train_end": str(train_df["time"].iloc[-1])[:10] if "time" in train_df.columns else None,
            "test_start": str(test_df["time"].iloc[0])[:10] if "time" in test_df.columns else None,
            "test_end": str(test_df["time"].iloc[-1])[:10] if "time" in test_df.columns else None,
            "in_sample": {
                "total_return": in_sample.get("total_return", 0),
                "sharpe": in_sample.get("sharpe", 0),
                "max_drawdown": in_sample.get("max_drawdown", 0),
                "win_rate": in_sample.get("win_rate", 0),
                "trades": len(in_sample.get("trades") or []),
            },
            "out_sample": {
                "total_return": out_sample.get("total_return", 0),
                "sharpe": out_sample.get("sharpe", 0),
                "max_drawdown": out_sample.get("max_drawdown", 0),
                "win_rate": out_sample.get("win_rate", 0),
                "trades": len(out_sample.get("trades") or []),
            },
        })

    if not folds:
        return {"error": "Walk-forward produced no valid folds"}

    oos_returns = [f["out_sample"]["total_return"] for f in folds if "out_sample" in f]
    oos_sharpes = [f["out_sample"]["sharpe"] for f in folds if "out_sample" in f]

    return {
        "n_splits": n_splits,
        "train_ratio": train_ratio,
        "folds": folds,
        "summary": {
            "avg_oos_return": round(float(np.mean(oos_returns)), 2) if oos_returns else 0,
            "avg_oos_sharpe": round(float(np.mean(oos_sharpes)), 2) if oos_sharpes else 0,
            "positive_oos_folds": sum(1 for r in oos_returns if r > 0),
            "total_folds": len(oos_returns),
            "consistency_pct": round(
                sum(1 for r in oos_returns if r > 0) / max(len(oos_returns), 1) * 100, 1
            ),
        },
    }


def compare_backtest_results(runs: list[dict]) -> dict[str, Any]:
    """Side-by-side comparison of multiple backtest runs."""
    if not runs:
        return {"error": "No runs to compare"}

    metrics = [
        "total_return", "cagr", "sharpe", "sortino", "max_drawdown",
        "win_rate", "profit_factor", "expectancy",
    ]

    comparison: list[dict] = []
    for i, run in enumerate(runs):
        label = run.get("label") or run.get("symbol") or f"Run {i + 1}"
        row = {"label": label, "symbol": run.get("symbol"), "period": run.get("period")}
        for m in metrics:
            row[m] = run.get(m, 0)
        row["trades"] = len(run.get("trades") or [])
        row["equity_curve"] = run.get("equity_curve") or []
        row["monthly_returns"] = run.get("monthly_returns") or compute_monthly_returns_by_year(
            run.get("equity_curve") or []
        )
        comparison.append(row)

    best_sharpe = max(comparison, key=lambda r: r.get("sharpe", 0))
    best_return = max(comparison, key=lambda r: r.get("total_return", 0))
    lowest_dd = min(comparison, key=lambda r: r.get("max_drawdown", 0))

    return {
        "runs": comparison,
        "rankings": {
            "best_sharpe": best_sharpe["label"],
            "best_return": best_return["label"],
            "lowest_drawdown": lowest_dd["label"],
        },
        "count": len(comparison),
    }
