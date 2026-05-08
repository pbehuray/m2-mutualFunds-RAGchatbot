"""
Caching implementation using Redis.
If Redis is not available, falls back to in-memory caching.
"""

import json
import hashlib
import os
from typing import Optional, Any
import time


class CacheBackend:
    """Base cache backend."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds."""
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache for fallback when Redis is not available."""
    
    def __init__(self):
        self.cache: Dict[str, tuple] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds."""
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return True
            else:
                del self.cache[key]
        return False


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        try:
            import redis
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.client.ping()  # Test connection
            self.available = True
        except Exception as e:
            print(f"Redis not available: {e}. Falling back to in-memory cache.")
            self.available = False
            self.fallback = MemoryCache()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if self.available:
            try:
                value = self.client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        return self.fallback.get(key) if hasattr(self, 'fallback') else None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds."""
        serialized = json.dumps(value)
        if self.available:
            try:
                self.client.setex(key, ttl, serialized)
                return True
            except Exception:
                pass
        if hasattr(self, 'fallback'):
            return self.fallback.set(key, value, ttl)
        return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self.available:
            try:
                self.client.delete(key)
                return True
            except Exception:
                pass
        if hasattr(self, 'fallback'):
            return self.fallback.delete(key)
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if self.available:
            try:
                return bool(self.client.exists(key))
            except Exception:
                pass
        if hasattr(self, 'fallback'):
            return self.fallback.exists(key)
        return False


def generate_cache_key(query: str, scheme: Optional[str] = None) -> str:
    """
    Generate cache key from query and scheme.
    
    Args:
        query: User query
        scheme: Optional scheme name
        
    Returns:
        Cache key hash
    """
    key_data = f"{query}|{scheme or ''}"
    return hashlib.md5(key_data.encode()).hexdigest()


# Global cache instance
cache = None


def get_cache() -> CacheBackend:
    """
    Get cache instance (Redis or fallback to in-memory).
    
    Returns:
        Cache backend instance
    """
    global cache
    if cache is None:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        cache = RedisCache(host=redis_host, port=redis_port)
    return cache
