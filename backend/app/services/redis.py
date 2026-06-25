"""
Redis client factory – provides a shared async Redis connection pool.

Usage:
    from app.services.redis import get_redis

    redis = await get_redis()
    await redis.set("key", "value", ex=3600)
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings

# Module-level connection pool – lazily initialised on first call.
_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """
    Return the shared async Redis client (creates it on first call).

    The connection pool is reused for the lifetime of the process so we
    don't open/close TCP sockets on every request.
    """
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # always return str, not bytes
        )
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool (call on app shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
