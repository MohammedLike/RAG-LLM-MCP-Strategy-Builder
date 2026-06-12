import json
from ..config import settings

try:
    import redis.asyncio as aioredis
    _redis_available = True
except ImportError:
    _redis_available = False


class ConversationMemory:
    """Redis-backed conversation memory with sliding window."""

    def __init__(self):
        self._redis = None
        self._local: dict[str, list[dict]] = {}

    async def _get_redis(self):
        if not _redis_available:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def get_history(self, session_id: str, max_messages: int = 20) -> list[dict]:
        r = await self._get_redis()
        if r:
            try:
                key = f"chat:{session_id}"
                data = await r.lrange(key, 0, max_messages - 1)
                return [json.loads(m) for m in data] if data else []
            except Exception:
                pass
        return self._local.get(session_id, [])[-max_messages:]

    async def add_message(self, session_id: str, role: str, content: str):
        msg = {"role": role, "content": content, "timestamp": __import__('datetime').datetime.utcnow().isoformat()}
        r = await self._get_redis()
        if r:
            try:
                key = f"chat:{session_id}"
                await r.lpush(key, json.dumps(msg))
                await r.ltrim(key, 0, 19)
                await r.expire(key, 86400)
                return
            except Exception:
                pass
        if session_id not in self._local:
            self._local[session_id] = []
        self._local[session_id].append(msg)
        if len(self._local[session_id]) > 20:
            self._local[session_id] = self._local[session_id][-20:]

    async def clear(self, session_id: str):
        r = await self._get_redis()
        if r:
            try:
                await r.delete(f"chat:{session_id}")
                return
            except Exception:
                pass
        self._local.pop(session_id, None)


memory = ConversationMemory()
