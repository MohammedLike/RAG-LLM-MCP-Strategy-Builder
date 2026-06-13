"""Redis-backed task store for async jobs (survives API restarts)."""

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
_PREFIX = "strykex:task:"
_TTL = 86400 * 2  # 48 hours


class TaskStore:
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

    def _key(self, task_id: str) -> str:
        return f"{_PREFIX}{task_id}"

    async def create(self, task_id: str, meta: dict | None = None) -> dict:
        state = {
            "task_id": task_id,
            "status": "running",
            "result": None,
            "error": None,
            "meta": meta or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._save(task_id, state)
        return state

    async def complete(self, task_id: str, result: Any) -> dict:
        state = await self.get(task_id) or {"task_id": task_id}
        state["status"] = "completed"
        state["result"] = result
        state["updated_at"] = datetime.utcnow().isoformat()
        await self._save(task_id, state)
        return state

    async def fail(self, task_id: str, error: str) -> dict:
        state = await self.get(task_id) or {"task_id": task_id}
        state["status"] = "failed"
        state["error"] = error
        state["updated_at"] = datetime.utcnow().isoformat()
        await self._save(task_id, state)
        return state

    async def get(self, task_id: str) -> dict | None:
        r = await self._client()
        key = self._key(task_id)
        if r:
            try:
                raw = await r.get(key)
                return json.loads(raw) if raw else None
            except Exception:
                pass
        return _local.get(key)

    async def _save(self, task_id: str, state: dict) -> None:
        key = self._key(task_id)
        payload = json.dumps(state, default=str)
        r = await self._client()
        if r:
            try:
                await r.setex(key, _TTL, payload)
                return
            except Exception:
                pass
        _local[key] = state


task_store = TaskStore()
