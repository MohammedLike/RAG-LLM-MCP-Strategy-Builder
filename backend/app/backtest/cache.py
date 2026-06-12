import hashlib
import json
from ..config import settings

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

class BacktestCache:
    def __init__(self):
        self._redis = None
        self._local_cache = {}

    async def _get_redis(self):
        if aioredis is None:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception:
                pass
        return self._redis

    def _make_key(self, symbol: str, period: str, strategy_spec: dict) -> str:
        raw = f"{symbol}:{period}:{json.dumps(strategy_spec, sort_keys=True)}"
        h = hashlib.md5(raw.encode()).hexdigest()
        return f"backtest:{symbol}:{period}:{h}"

    async def get(self, symbol: str, period: str, strategy_spec: dict):
        key = self._make_key(symbol, period, strategy_spec)
        r = await self._get_redis()
        if r:
            try:
                data = await r.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        return self._local_cache.get(key)

    async def set(self, symbol: str, period: str, strategy_spec: dict, result: dict, ttl: int = 3600):
        key = self._make_key(symbol, period, strategy_spec)
        self._local_cache[key] = result
        r = await self._get_redis()
        if r:
            try:
                await r.setex(key, ttl, json.dumps(result, default=str))
            except Exception:
                pass

    async def invalidate(self, symbol: str = None, period: str = None):
        if symbol and period:
            key_prefix = f"backtest:{symbol}:{period}:"
            self._local_cache = {k: v for k, v in self._local_cache.items() if not k.startswith(key_prefix)}
        else:
            self._local_cache = {}

backtest_cache = BacktestCache()
