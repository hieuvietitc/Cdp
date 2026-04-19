"""
Write-key validation for the Collector API.

Strategy (fast path first):
  1. Redis cache hit "1"  → valid, allow
  2. Redis cache hit "0"  → invalid, reject 401
  3. Cache miss           → query DB, cache result for 5 min, then allow/reject

This ensures:
  - Hot path (known keys) is sub-millisecond via Redis
  - Unknown/invalid keys are rejected after at most one DB round-trip per 5 min
  - No race condition where an unrecognised key is silently accepted
"""
from fastapi import HTTPException

from cdp_shared.redis_client import get_redis

_VALID_KEY_CACHE_TTL = 300    # 5 minutes
_INVALID_KEY_CACHE_TTL = 60   # cache rejections for 1 minute (avoid DB hammering)
_CACHE_VALID = "1"
_CACHE_INVALID = "0"


def validate_write_key(write_key: str) -> None:
    r = get_redis()
    cache_key = f"cdp:write_key:{write_key}"
    cached = r.get(cache_key)

    if cached == _CACHE_VALID:
        return
    if cached == _CACHE_INVALID:
        raise HTTPException(status_code=401, detail="Invalid write_key")

    # Cache miss — check DB
    is_valid = _lookup_db(write_key)
    if is_valid:
        r.setex(cache_key, _VALID_KEY_CACHE_TTL, _CACHE_VALID)
    else:
        r.setex(cache_key, _INVALID_KEY_CACHE_TTL, _CACHE_INVALID)
        raise HTTPException(status_code=401, detail="Invalid write_key")


def _lookup_db(write_key: str) -> bool:
    from cdp_shared.db import SessionLocal
    from cdp_shared.models.source import Source
    from sqlalchemy import select
    with SessionLocal() as db:
        row = db.execute(
            select(Source.id).where(Source.write_key == write_key, Source.is_active == True)
        ).scalar_one_or_none()
        return row is not None
