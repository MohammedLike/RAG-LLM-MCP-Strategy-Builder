import json
from functools import wraps

from ..config import settings

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

_local_cache: dict[str, str] = {}


def _client():
    if redis is None:
        return None
    try:
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def redis_cache(ttl_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_args = [str(arg) for arg in args if not hasattr(arg, "__dict__")]
            key_kwargs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = f"cache:{func.__name__}:{':'.join(key_args)}:{':'.join(key_kwargs)}"

            client = _client()
            if client:
                try:
                    cached_val = await client.get(cache_key)
                    if cached_val:
                        return json.loads(cached_val)
                except Exception:
                    pass
            elif cache_key in _local_cache:
                return json.loads(_local_cache[cache_key])

            result = await func(*args, **kwargs)

            if result is not None:
                if hasattr(result, "to_dict"):
                    cache_val = result.to_dict(orient="records")
                else:
                    cache_val = result
                payload = json.dumps(cache_val, default=str)
                if client:
                    try:
                        await client.setex(cache_key, ttl_seconds, payload)
                    except Exception:
                        pass
                else:
                    _local_cache[cache_key] = payload

            return result

        return wrapper

    return decorator
