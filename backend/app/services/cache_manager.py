"""
Redis Cache Manager.

Provides caching functionality for SERP results and other data.
"""

import json
from datetime import timedelta
from typing import Optional, Any

import redis.asyncio as redis

from app.config import settings


class CacheManager:
    """Manager for Redis caching operations."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis server."""
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            try:
                await self._client.ping()
                self._connected = True
            except redis.ConnectionError:
                self._connected = False
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected:
            await self.connect()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        await self._ensure_connected()
        if not self._connected:
            return None
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire_days: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire_days: Expiration in days (default from settings)
            
        Returns:
            True if successful
        """
        await self._ensure_connected()
        if not self._connected:
            return False
        
        try:
            expire_days = expire_days or settings.cache_expire_days
            serialized = json.dumps(value, default=str)
            await self._client.setex(
                key,
                timedelta(days=expire_days),
                serialized,
            )
            return True
        except (redis.RedisError, json.JSONDecodeError):
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        await self._ensure_connected()
        if not self._connected:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except redis.RedisError:
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        await self._ensure_connected()
        if not self._connected:
            return False
        
        try:
            return await self._client.exists(key) > 0
        except redis.RedisError:
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get time-to-live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, or None if key doesn't exist
        """
        await self._ensure_connected()
        if not self._connected:
            return None
        
        try:
            ttl = await self._client.ttl(key)
            return ttl if ttl > 0 else None
        except redis.RedisError:
            return None
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "serp:*")
            
        Returns:
            Number of keys deleted
        """
        await self._ensure_connected()
        if not self._connected:
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        await self._ensure_connected()
        if not self._connected:
            return {"connected": False}
        
        try:
            info = await self._client.info("memory")
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "peak_memory": info.get("used_memory_peak_human", "N/A"),
            }
        except redis.RedisError:
            return {"connected": False}


# Singleton instance
cache_manager = CacheManager()
