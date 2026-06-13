"""Parameter grid optimization for strategy backtests."""

from __future__ import annotations

import copy
from typing import Any

from .engine import BacktestEngine


def _set_nested(spec: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    obj = spec
    for part in parts[:-1]:
        if part.endswith("]"):
            name, idx = part[:-1].split("[")
            obj = obj[name][int(idx)]
        else:
            obj = obj.setdefault(part, {})
    last = parts[-1]
    if last.endswith("]"):
        name, idx = last[:-1].split("[")
        obj[name][int(idx)] = value
    else:
        obj[last] = value


def build_param_combinations(grid: dict[str, list]) -> list[dict]:
    if not grid:
        return [{}]
    keys = list(grid.keys())
    combos: list[dict] = [{}]

    for key in keys:
        new_combos: list[dict] = []
        for combo in combos:
            for val in grid[key]:
                c = copy.deepcopy(combo)
                c[key] = val
                new_combos.append(c)
        combos = new_combos
    return combos


def apply_params(base_spec: dict, params: dict) -> dict:
    spec = copy.deepcopy(base_spec)
    for path, value in params.items():
        _set_nested(spec, path, value)
    return spec


def run_grid_search(
    df,
    base_spec: dict,
    param_grid: dict[str, list],
    max_runs: int = 50,
) -> dict[str, Any]:
    engine = BacktestEngine()
    combos = build_param_combinations(param_grid)[:max_runs]
    rows: list[dict] = []
    best: dict | None = None
    best_score = float("-inf")

    for params in combos:
        spec = apply_params(base_spec, params)
        try:
            result = engine.run(df.copy(), spec)
        except Exception as e:
            rows.append({"params": params, "error": str(e)})
            continue

        row = {
            "params": params,
            "total_return": result.get("total_return", 0),
            "sharpe": result.get("sharpe", 0),
            "max_drawdown": result.get("max_drawdown", 0),
            "win_rate": result.get("win_rate", 0),
            "profit_factor": result.get("profit_factor", 0),
            "trades": len(result.get("trades") or []),
        }
        rows.append(row)
        score = row["sharpe"] if row["sharpe"] else row["total_return"]
        if score > best_score:
            best_score = score
            best = row

    rows.sort(key=lambda r: r.get("sharpe", 0) or r.get("total_return", 0), reverse=True)
    return {
        "optimization_grid": rows,
        "best_params": best.get("params") if best else {},
        "best_metrics": {k: best[k] for k in ("total_return", "sharpe", "max_drawdown", "win_rate")} if best else {},
        "runs": len(rows),
    }
