"""Persist user Pine Script sources in Postgres."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from .session import async_session, is_db_available


def _slug_for(source: str, name: str | None = None) -> str:
    base = (name or source).replace(" ", "_").lower()[:40]
    return f"{source}_{uuid.uuid4().hex[:8]}" if not name else f"{base}_{uuid.uuid4().hex[:6]}"


async def save_pine_script(
    pine_script: str,
    *,
    name: str | None = None,
    source: str = "upload",
    symbol: str | None = None,
    period: str | None = None,
    resolution: str | None = None,
    strategy_spec: dict | None = None,
    prompt: str | None = None,
    slug: str | None = None,
    metadata: dict | None = None,
) -> dict | None:
    if not is_db_available() or async_session is None or not pine_script.strip():
        return None

    script_slug = slug or _slug_for(source, name)
    display_name = name or script_slug.replace("_", " ").title()
    now = datetime.utcnow()

    async with async_session() as session:
        row = (
            await session.execute(
                text(
                    """
                    INSERT INTO pine_scripts (
                        slug, name, source, pine_script, strategy_spec,
                        symbol, period, resolution, prompt, metadata, created_at, updated_at
                    ) VALUES (
                        :slug, :name, :source, :pine_script, CAST(:strategy_spec AS jsonb),
                        :symbol, :period, :resolution, :prompt, CAST(:metadata AS jsonb),
                        :created_at, :updated_at
                    )
                    ON CONFLICT (slug) DO UPDATE SET
                        pine_script = EXCLUDED.pine_script,
                        strategy_spec = EXCLUDED.strategy_spec,
                        symbol = EXCLUDED.symbol,
                        period = EXCLUDED.period,
                        resolution = EXCLUDED.resolution,
                        prompt = EXCLUDED.prompt,
                        metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id, slug, name, source, symbol, period, resolution, created_at
                    """
                ),
                {
                    "slug": script_slug,
                    "name": display_name,
                    "source": source,
                    "pine_script": pine_script,
                    "strategy_spec": _json_or_null(strategy_spec),
                    "symbol": symbol,
                    "period": period,
                    "resolution": resolution,
                    "prompt": prompt,
                    "metadata": _json_or_null(metadata),
                    "created_at": now,
                    "updated_at": now,
                },
            )
        ).mappings().first()
        await session.commit()
        return _serialize_pine_row(row, len(pine_script)) if row else None


async def list_pine_scripts(limit: int = 100) -> list[dict]:
    if not is_db_available() or async_session is None:
        return []

    async with async_session() as session:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, source, symbol, period, resolution,
                           LENGTH(pine_script) AS size, created_at, updated_at
                    FROM pine_scripts
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
        ).mappings().all()
        return [_serialize_pine_row(r, r.get("size")) for r in rows]


async def get_pine_script(script_id: str) -> dict | None:
    if not is_db_available() or async_session is None:
        return None

    async with async_session() as session:
        row = (
            await session.execute(
                text(
                    """
                    SELECT id, slug, name, source, pine_script, strategy_spec,
                           symbol, period, resolution, prompt, metadata, created_at, updated_at
                    FROM pine_scripts
                    WHERE slug = :slug OR id::text = :slug
                    LIMIT 1
                    """
                ),
                {"slug": script_id},
            )
        ).mappings().first()
        if not row:
            return None
        out = _serialize_pine_row(row, len(row.get("pine_script") or ""))
        out["content"] = row["pine_script"]
        out["strategy_spec"] = row.get("strategy_spec")
        out["prompt"] = row.get("prompt")
        out["metadata"] = row.get("metadata")
        return out


async def delete_pine_script(script_id: str) -> bool:
    if not is_db_available() or async_session is None:
        return False

    async with async_session() as session:
        result = await session.execute(
            text("DELETE FROM pine_scripts WHERE slug = :slug OR id::text = :slug"),
            {"slug": script_id},
        )
        await session.commit()
        return result.rowcount > 0


def _json_or_null(value: Any) -> str | None:
    if value is None:
        return None
    import json

    return json.dumps(value)


def _serialize_pine_row(row: dict, size: int | None = None) -> dict:
    created = row.get("created_at")
    updated = row.get("updated_at") or created
    return {
        "id": str(row["id"]) if row.get("id") else row.get("slug"),
        "slug": row.get("slug"),
        "name": row.get("name"),
        "source": row.get("source"),
        "symbol": row.get("symbol"),
        "period": row.get("period"),
        "resolution": row.get("resolution"),
        "filename": f"{row.get('slug')}.pine",
        "size": size or 0,
        "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        "updated": updated.isoformat() if hasattr(updated, "isoformat") else updated,
    }
