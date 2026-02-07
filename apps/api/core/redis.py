from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from apps.api.core.config import get_settings

settings = get_settings()
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def cache_get(key: str) -> Any | None:
    val = await redis_client.get(key)
    if val:
        return json.loads(val)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(key: str) -> None:
    await redis_client.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)
