"""Redis client and connection lifecycle utilities."""

import time

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger


class RedisManager:
    """Manages asynchronous Redis connections for caching and message queuing."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_uri,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_connectivity(self) -> tuple[bool, float, str]:
        """Ping Redis and return (is_healthy, latency_ms, message)."""
        start = time.perf_counter()
        try:
            client = await self.get_client()
            pong = await client.ping()
            latency = (time.perf_counter() - start) * 1000
            if pong:
                return True, round(latency, 2), "Redis cache/queue responsive."
            return False, round(latency, 2), "Unexpected response from Redis ping."
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.info(f"Redis not reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e})")
            return False, round(latency, 2), f"Redis unavailable: {e}"


redis_manager = RedisManager()
