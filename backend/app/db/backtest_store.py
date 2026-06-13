"""Persist backtest runs in Postgres."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from ..backtest.metrics import compute_monthly_returns_by_year
from .session import async_session, is_db_available


def _extract_metrics(result: dict) -> dict:
    return {
        "total_return": result.get("total_return"),
        "win_rate": result.get("win_rate"),
        "sharpe": result.get("sharpe"),
        "sortino": result.get("sortino"),
        "max_drawdown": result.get("max_drawdown"),
        "cagr": result.get("cagr"),
        "profit_factor": result.get("profit_factor"),
        "expectancy": result.get("expectancy"),
        "total_trades": len(result.get("trades") or []),
        "data_rows": result.get("data_rows"),
        "data_start": result.get("data_start"),
        "data_end": result.get("data_end"),
        "data_source": result.get("data_source"),
        "cached": result.get("cached", False),
        "timestamp": result.get("timestamp") or datetime.utcnow().isoformat(),
    }


async def save_backtest_run(
    result: dict,
    *,
    strategy_spec: dict,
    symbol: str,
    period: str,
    resolution: str = "1d",
    strategy_label: str | None = None,
    source: str = "engine",
    pine_script_id: str | None = None,
    strategy_id: str | None = None,
    user_request: dict | None = None,
    status: str = "completed",
) -> str | None:
    if not is_db_available() or async_session is None:
        return None

    if result.get("error"):
        status = "failed"

    equity_curve = result.get("equity_curve") or []
    monthly_returns = result.get("monthly_returns")
    if monthly_returns is None and equity_curve:
        monthly_returns = compute_monthly_returns_by_year(equity_curve)

    metrics = _extract_metrics(result)
    now = datetime.utcnow()
    backtest_id = str(uuid.uuid4())

    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO backtests (
                    id, strategy_id, pine_script_id, user_request_json, status,
                    symbol, period, resolution, strategy_spec, strategy_label, source,
                    metrics, equity_curve, trade_log, drawdown_series, monthly_returns,
                    error_message, started_at, completed_at
                ) VALUES (
                    CAST(:id AS uuid),
                    CAST(:strategy_id AS uuid),
                    CAST(:pine_script_id AS uuid),
                    CAST(:user_request AS jsonb),
                    :status,
                    :symbol, :period, :resolution,
                    CAST(:strategy_spec AS jsonb),
                    :strategy_label, :source,
                    CAST(:metrics AS jsonb),
                    CAST(:equity_curve AS jsonb),
                    CAST(:trade_log AS jsonb),
                    CAST(:drawdown_series AS jsonb),
                    CAST(:monthly_returns AS jsonb),
                    :error_message,
                    :started_at, :completed_at
                )
                """
            ),
            {
                "id": backtest_id,
                "strategy_id": strategy_id,
                "pine_script_id": pine_script_id,
                "user_request": _json_or_null(user_request),
                "status": status,
                "symbol": symbol,
                "period": period,
                "resolution": resolution,
                "strategy_spec": json.dumps(strategy_spec),
                "strategy_label": strategy_label,
                "source": source,
                "metrics": json.dumps(metrics),
                "equity_curve": json.dumps(equity_curve),
                "trade_log": json.dumps(result.get("trades") or []),
                "drawdown_series": json.dumps(result.get("drawdown") or []),
                "monthly_returns": json.dumps(monthly_returns or {}),
                "error_message": result.get("error"),
                "started_at": now,
                "completed_at": now if status in ("completed", "failed") else None,
            },
        )
        await session.commit()
        return backtest_id


async def list_backtest_runs(limit: int = 50, symbol: str | None = None) -> list[dict]:
    if not is_db_available() or async_session is None:
        return []

    query = """
        SELECT b.id, b.symbol, b.period, b.resolution, b.strategy_label, b.source,
               b.status, b.metrics, b.started_at, b.completed_at,
               b.pine_script_id, p.slug AS pine_slug, p.name AS pine_name
        FROM backtests b
        LEFT JOIN pine_scripts p ON p.id = b.pine_script_id
    """
    params: dict[str, Any] = {"limit": limit}
    if symbol:
        query += " WHERE b.symbol = :symbol"
        params["symbol"] = symbol
    query += " ORDER BY b.started_at DESC NULLS LAST LIMIT :limit"

    async with async_session() as session:
        rows = (await session.execute(text(query), params)).mappings().all()
        return [_serialize_history_row(r) for r in rows]


async def get_backtest_run(backtest_id: str) -> dict | None:
    if not is_db_available() or async_session is None:
        return None

    async with async_session() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT b.*, p.slug AS pine_slug, p.name AS pine_name, p.pine_script
                    FROM backtests b
                    LEFT JOIN pine_scripts p ON p.id = b.pine_script_id
                    WHERE b.id::text = :id
                    LIMIT 1
                    """
                ),
                {"id": backtest_id},
            )
        ).mappings().first()
        if not row:
            return None
        return _serialize_full_row(row)


def _json_or_null(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _serialize_history_row(row: dict) -> dict:
    metrics = row.get("metrics") or {}
    started = row.get("started_at")
    return {
        "id": str(row["id"]),
        "timestamp": started.isoformat() if hasattr(started, "isoformat") else started,
        "strategy": row.get("strategy_label") or row.get("pine_name") or "Custom Strategy",
        "symbol": row.get("symbol"),
        "period": row.get("period"),
        "interval": row.get("resolution"),
        "source": row.get("source"),
        "status": row.get("status"),
        "total_return": metrics.get("total_return"),
        "win_rate": metrics.get("win_rate"),
        "max_drawdown": metrics.get("max_drawdown"),
        "trades": metrics.get("total_trades", 0),
        "pine_script_id": str(row["pine_script_id"]) if row.get("pine_script_id") else None,
        "pine_slug": row.get("pine_slug"),
    }


def _serialize_full_row(row: dict) -> dict:
    metrics = row.get("metrics") or {}
    history = _serialize_history_row(row)
    return {
        **history,
        "strategy_spec": row.get("strategy_spec"),
        "user_request": row.get("user_request_json"),
        "equity_curve": row.get("equity_curve") or [],
        "trades": row.get("trade_log") or [],
        "drawdown": row.get("drawdown_series") or [],
        "monthly_returns": row.get("monthly_returns") or {},
        "metrics": metrics,
        "pine_script": row.get("pine_script"),
        "error": row.get("error_message"),
        "result": {
            **metrics,
            "symbol": row.get("symbol"),
            "period": row.get("period"),
            "interval": row.get("resolution"),
            "strategy_spec": row.get("strategy_spec"),
            "equity_curve": row.get("equity_curve") or [],
            "trades": row.get("trade_log") or [],
            "drawdown": row.get("drawdown_series") or [],
            "monthly_returns": row.get("monthly_returns") or {},
        },
    }
