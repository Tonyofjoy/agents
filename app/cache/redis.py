import json
from typing import Any, Dict, Optional, Union
import redis.asyncio as redis


class RedisClient:
    """
    Async Redis client for caching and session management.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        url: Optional[str] = None,
    ):
        """
        Initialize Redis client.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database
            password: Redis password
            url: Redis URL (takes precedence if provided)
        """
        if url:
            self.redis = redis.from_url(url)
        else:
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return await self.redis.get(key)

    async def set(
        self, key: str, value: str, expire: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration."""
        if expire:
            return await self.redis.setex(key, expire, value)
        return await self.redis.set(key, value)

    async def delete(self, key: str) -> int:
        """Delete key from Redis."""
        return await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        return await self.redis.exists(key)

    async def store_session_data(
        self, session_id: str, data: Dict[str, Any], expire: int = 86400
    ) -> bool:
        """
        Store session data in Redis.
        
        Args:
            session_id: Unique session identifier
            data: Session data to store
            expire: Session expiration time in seconds (default: 24 hours)
        """
        key = f"session:{session_id}"
        value = json.dumps(data)
        return await self.set(key, value, expire)

    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Unique session identifier
        """
        key = f"session:{session_id}"
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete_session(self, session_id: str) -> int:
        """
        Delete session data from Redis.
        
        Args:
            session_id: Unique session identifier
        """
        key = f"session:{session_id}"
        return await self.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()
