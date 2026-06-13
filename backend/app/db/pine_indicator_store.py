"""Persist and query TradingView indicator catalog for Pine AI."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import text

from ..strategies.pine_indicator_catalog import build_indicator_catalog, format_catalog_for_llm
from .session import async_session, is_db_available

_llm_cache: str | None = None


async def seed_pine_indicators() -> int:
    """Upsert full indicator catalog. Returns number of rows upserted."""
    global _llm_cache
    _llm_cache = None

    if not is_db_available() or async_session is None:
        return 0

    catalog = build_indicator_catalog()
    now = datetime.utcnow()
    count = 0

    async with async_session() as session:
        for row in catalog:
            await session.execute(
                text(
                    """
                    INSERT INTO pine_indicators (
                        name, pine_name, long_name, category, description,
                        params, inputs, backtest_supported, source, created_at, updated_at
                    ) VALUES (
                        :name, :pine_name, :long_name, :category, :description,
                        CAST(:params AS jsonb), CAST(:inputs AS jsonb),
                        :backtest_supported, :source, :created_at, :updated_at
                    )
                    ON CONFLICT (name) DO UPDATE SET
                        pine_name = EXCLUDED.pine_name,
                        long_name = EXCLUDED.long_name,
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        params = EXCLUDED.params,
                        inputs = EXCLUDED.inputs,
                        backtest_supported = EXCLUDED.backtest_supported,
                        source = EXCLUDED.source,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "name": row["name"],
                    "pine_name": row["pine_name"],
                    "long_name": row.get("long_name"),
                    "category": row.get("category", "Other"),
                    "description": row.get("description"),
                    "params": json.dumps(row.get("params") or {}),
                    "inputs": json.dumps(row.get("inputs") or []),
                    "backtest_supported": bool(row.get("backtest_supported")),
                    "source": row.get("source", "tradingview"),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            count += 1
        await session.commit()

    return count


async def list_pine_indicators(
    *,
    category: str | None = None,
    backtest_only: bool = False,
    limit: int = 500,
) -> list[dict[str, Any]]:
    if not is_db_available() or async_session is None:
        return build_indicator_catalog()

    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if category:
        clauses.append("category = :category")
        params["category"] = category
    if backtest_only:
        clauses.append("backtest_supported = true")

    sql = f"""
        SELECT name, pine_name, long_name, category, description,
               params, inputs, backtest_supported, source
        FROM pine_indicators
        WHERE {' AND '.join(clauses)}
        ORDER BY category, name
        LIMIT :limit
    """

    async with async_session() as session:
        result = await session.execute(text(sql), params)
        rows = result.mappings().all()

    if not rows:
        return build_indicator_catalog()

    return [dict(r) for r in rows]


async def get_indicator_context_for_llm(
    *,
    backtest_only: bool = False,
    max_items: int = 120,
) -> str:
    """Load indicator reference text for Pine AI prompts."""
    global _llm_cache

    cache_key = f"{backtest_only}:{max_items}"
    if _llm_cache and getattr(get_indicator_context_for_llm, "_cache_key", None) == cache_key:
        return _llm_cache

    indicators = await list_pine_indicators(backtest_only=backtest_only, limit=max_items + 50)
    text_block = format_catalog_for_llm(indicators, max_items=max_items, backtest_only=backtest_only)

    _llm_cache = text_block
    get_indicator_context_for_llm._cache_key = cache_key  # type: ignore[attr-defined]
    return text_block


async def indicator_count() -> int:
    if not is_db_available() or async_session is None:
        return len(build_indicator_catalog())

    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) AS n FROM pine_indicators"))
        row = result.mappings().first()
        return int(row["n"]) if row else 0
