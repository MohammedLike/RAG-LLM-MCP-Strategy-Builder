"""Track long-running OHLCV ingest jobs in Redis (with in-memory fallback)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..config import settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

_local: dict[str, dict] = {}


class IngestProgress:
    KEY = "strykex:ingest:current"

    def __init__(self) -> None:
        self._redis = None

    async def _client(self):
        if aioredis is None:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def start(self, total: int, job_type: str = "nse_bse_daily", metadata: dict | None = None) -> dict:
        state = {
            "status": "running",
            "job_type": job_type,
            "total_symbols": total,
            "completed_symbols": 0,
            "failed_symbols": [],
            "last_symbol": None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        await self._save(state)
        return state

    async def tick(self, symbol: str, ok: bool, rows: int = 0, error: str | None = None) -> dict:
        state = await self.get() or {}
        state["completed_symbols"] = int(state.get("completed_symbols", 0)) + 1
        state["last_symbol"] = symbol
        state["updated_at"] = datetime.utcnow().isoformat()
        if not ok:
            failures = list(state.get("failed_symbols") or [])
            failures.append({"symbol": symbol, "error": error or "no data", "rows": rows})
            state["failed_symbols"] = failures[-200:]
        await self._save(state)
        return state

    async def finish(self, status: str = "completed") -> dict:
        state = await self.get() or {}
        state["status"] = status
        state["updated_at"] = datetime.utcnow().isoformat()
        await self._save(state)
        return state

    async def get(self) -> dict | None:
        r = await self._client()
        if r:
            try:
                raw = await r.get(self.KEY)
                return json.loads(raw) if raw else None
            except Exception:
                pass
        return _local.get(self.KEY)

    async def _save(self, state: dict[str, Any]) -> None:
        r = await self._client()
        payload = json.dumps(state)
        if r:
            try:
                await r.set(self.KEY, payload, ex=86400 * 7)
                return
            except Exception:
                pass
        _local[self.KEY] = state


ingest_progress = IngestProgress()
