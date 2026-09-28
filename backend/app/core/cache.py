import functools
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

from redis.asyncio import Redis

from app.core.config import get_settings

log = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def cache_get_json(key: str) -> Any | None:
    try:
        raw = await get_redis().get(key)
    except Exception as exc:  # cache down shouldn't break the request
        log.warning("cache get failed for %s: %s", key, exc)
        return None
    return json.loads(raw) if raw else None


async def cache_set_json(key: str, value: Any, ttl: int) -> None:
    try:
        await get_redis().set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:
        log.warning("cache set failed for %s: %s", key, exc)


def cached(
    prefix: str, ttl: int
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Cache an async fn by its first arg (e.g. a domain).

    Pass force=True to skip the lookup and refresh the entry.
    Return value has to be json-serialisable.
    """

    def deco(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            force = bool(kwargs.pop("force", False))
            key = f"{prefix}:{args[0]}" if args else prefix
            if not force:
                hit = await cache_get_json(key)
                if hit is not None:
                    return hit
            result = await fn(*args, **kwargs)
            if result is not None:
                await cache_set_json(key, result, ttl)
            return result

        return wrapper

    return deco
