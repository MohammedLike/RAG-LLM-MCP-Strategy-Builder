import json
import redis.asyncio as redis
from functools import wraps
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def redis_cache(ttl_seconds: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            # Ignore 'self' if it's a method
            key_args = [str(arg) for arg in args if not hasattr(arg, '__dict__')]
            key_kwargs = [f"{k}={v}" for k, v in kwargs.items()]
            cache_key = f"cache:{func.__name__}:{':'.join(key_args)}:{':'.join(key_kwargs)}"
            
            cached_val = await redis_client.get(cache_key)
            if cached_val:
                return json.loads(cached_val)
                
            result = await func(*args, **kwargs)
            
            if result:
                # If it's a pandas DataFrame, convert to dict first
                if hasattr(result, 'to_dict'):
                    cache_val = result.to_dict(orient='records')
                else:
                    cache_val = result
                    
                await redis_client.setex(cache_key, ttl_seconds, json.dumps(cache_val))
                
            return result
        return wrapper
    return decorator
