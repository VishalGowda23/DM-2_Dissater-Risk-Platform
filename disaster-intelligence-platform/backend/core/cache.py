"""
Redis cache configuration and utilities
"""
import redis
import json
import pickle
import hashlib
from typing import Optional, Any, Union
from datetime import datetime, timedelta
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key from prefix and arguments"""
    key_data = f"{prefix}:{str(args)}:{str(kwargs)}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        data = redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache with TTL"""
    try:
        ttl = ttl or settings.CACHE_TTL
        serialized = pickle.dumps(value)
        redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


def clear_cache_pattern(pattern: str) -> int:
    """Clear all keys matching pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache clear pattern error: {e}")
        return 0


def cache_result(prefix: str, ttl: int = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = get_cache_key(prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            cached = get_cache(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            set_cache(cache_key, result, ttl)
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            cache_key = get_cache_key(prefix, func.__name__, args, kwargs)
            cached = get_cache(cache_key)
            if cached is not None:
                return cached
            
            result = func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            
            return result
        
        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


def get_weather_cache_key(lat: float, lon: float) -> str:
    """Generate cache key for weather data"""
    return f"weather:{lat:.4f}:{lon:.4f}"


def cache_weather_data(lat: float, lon: float, data: dict, ttl: int = None) -> bool:
    """Cache weather data for a location"""
    key = get_weather_cache_key(lat, lon)
    return set_cache(key, data, ttl or settings.WEATHER_CACHE_TTL)


def get_cached_weather(lat: float, lon: float) -> Optional[dict]:
    """Get cached weather data for a location"""
    key = get_weather_cache_key(lat, lon)
    return get_cache(key)
