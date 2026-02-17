"""
Redis cache layer with weather-specific caching
Production-grade with connection error handling and fallbacks
"""
import redis
import json
import pickle
import hashlib
from typing import Optional, Any
from datetime import datetime
import logging

from app.db.config import settings

logger = logging.getLogger(__name__)

# Redis client with connection pooling
try:
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
except Exception as e:
    logger.warning(f"Redis connection init failed: {e}")
    redis_client = None


def _is_redis_available() -> bool:
    """Check if Redis is available"""
    if redis_client is None:
        return False
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate deterministic cache key"""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return f"dip:{hashlib.md5(key_data.encode()).hexdigest()}"


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache, returns None on miss or error"""
    if not _is_redis_available():
        return None
    try:
        data = redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    except Exception as e:
        logger.error(f"Cache get error for {key}: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache with TTL"""
    if not _is_redis_available():
        return False
    try:
        ttl = ttl or settings.CACHE_TTL
        serialized = pickle.dumps(value)
        redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.error(f"Cache set error for {key}: {e}")
        return False


def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    if not _is_redis_available():
        return False
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


def clear_cache_pattern(pattern: str) -> int:
    """Clear all keys matching pattern"""
    if not _is_redis_available():
        return 0
    try:
        keys = redis_client.keys(f"dip:{pattern}")
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return 0


# --- Weather-specific cache ---

def get_weather_cache_key(lat: float, lon: float) -> str:
    """Generate cache key for weather data"""
    return f"dip:weather:{lat:.4f}:{lon:.4f}"


def cache_weather_data(lat: float, lon: float, data: dict, ttl: int = None) -> bool:
    """Cache weather data for a location"""
    key = get_weather_cache_key(lat, lon)
    return set_cache(key, data, ttl or settings.WEATHER_CACHE_TTL)


def get_cached_weather(lat: float, lon: float) -> Optional[dict]:
    """Get cached weather data for a location"""
    key = get_weather_cache_key(lat, lon)
    return get_cache(key)


# --- Risk score cache ---

def cache_risk_scores(ward_id: str, scores: dict, ttl: int = None) -> bool:
    """Cache computed risk scores for a ward"""
    key = f"dip:risk:{ward_id}"
    return set_cache(key, scores, ttl or settings.CACHE_TTL)


def get_cached_risk(ward_id: str) -> Optional[dict]:
    """Get cached risk scores for a ward"""
    key = f"dip:risk:{ward_id}"
    return get_cache(key)


# --- OSM data cache ---

def cache_osm_data(ward_id: str, data: dict) -> bool:
    """Cache OSM infrastructure data (24h TTL)"""
    key = f"dip:osm:{ward_id}"
    return set_cache(key, data, settings.OSM_CACHE_TTL)


def get_cached_osm(ward_id: str) -> Optional[dict]:
    """Get cached OSM data"""
    key = f"dip:osm:{ward_id}"
    return get_cache(key)
