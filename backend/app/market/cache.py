"""
Quant AI Agent — Redis Cache Layer

Provides a caching decorator and utility functions for market data.
TTLs vary by data type: live quotes (1s), OHLCV (5min), options chain (30s).
"""

import json
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()

# Global Redis client (lazy init)
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis async client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# ── TTL constants (seconds) ──
TTL_QUOTE = 1           # Live quotes: 1 second
TTL_OHLCV = 300         # Historical OHLCV: 5 minutes
TTL_OPTIONS = 30        # Options chain: 30 seconds
TTL_EXPIRY = 3600       # Expiry dates: 1 hour
TTL_GREEKS = 60         # Greeks computation: 1 minute
TTL_DEFAULT = 60        # Default: 1 minute


async def cache_get(key: str) -> Any | None:
    """Get value from cache. Returns None if miss."""
    redis = await get_redis()
    value = await redis.get(key)
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return None


async def cache_set(key: str, value: Any, ttl: int = TTL_DEFAULT) -> None:
    """Set value in cache with TTL."""
    redis = await get_redis()
    serialized = json.dumps(value, default=str)
    await redis.setex(key, ttl, serialized)


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    redis = await get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (use sparingly)."""
    redis = await get_redis()
    async for key in redis.scan_iter(match=pattern, count=100):
        await redis.delete(key)


def cached(
    key_prefix: str,
    ttl: int = TTL_DEFAULT,
    key_builder: Callable[..., str] | None = None,
):
    """
    Async cache decorator for market data functions.

    Usage:
        @cached("quote", ttl=TTL_QUOTE)
        async def get_quote(self, symbol: str) -> Quote:
            ...

        @cached("ohlcv", ttl=TTL_OHLCV, key_builder=lambda s, i, **kw: f"{s}:{i}")
        async def get_ohlcv(self, symbol, interval, ...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                # Skip 'self' argument
                func_args = args[1:] if args else args
                key_suffix = key_builder(*func_args, **kwargs)
            else:
                # Default: use all string/numeric positional args
                func_args = args[1:] if args else args
                key_parts = [str(a) for a in func_args if isinstance(a, (str, int, float))]
                key_suffix = ":".join(key_parts) if key_parts else "default"

            cache_key = f"market:{key_prefix}:{key_suffix}"

            # Try cache first
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss — call the function
            result = await func(*args, **kwargs)

            # Cache the result (convert dataclasses to dicts)
            if hasattr(result, "to_dict"):
                await cache_set(cache_key, result.to_dict(), ttl)
            elif hasattr(result, "to_json"):
                await cache_set(cache_key, result.to_json(), ttl)
            else:
                try:
                    await cache_set(cache_key, result, ttl)
                except TypeError:
                    pass  # Skip caching if not serializable

            return result

        return wrapper

    return decorator


# ── Pub/Sub for live market data broadcast ──

async def publish_market_update(channel: str, data: dict) -> None:
    """Publish a market data update to Redis Pub/Sub."""
    redis = await get_redis()
    await redis.publish(channel, json.dumps(data, default=str))


async def subscribe_market_updates(
    channels: list[str],
) -> aioredis.client.PubSub:
    """Subscribe to market data channels. Returns a PubSub instance."""
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(*channels)
    return pubsub
