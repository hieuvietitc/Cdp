from fastapi import HTTPException
from cdp_shared.redis_client import get_redis

_VALID_KEY_CACHE_TTL = 300  # 5 minutes


def validate_write_key(write_key: str) -> None:
    """Check write_key against Redis cache (populated from DB by processor on first use)."""
    r = get_redis()
    cache_key = f"cdp:write_key:{write_key}"
    result = r.get(cache_key)
    if result == "0":
        raise HTTPException(status_code=401, detail="Invalid write_key")
    # If not in cache, allow through — processor will validate and cache it
    # This keeps the collector hot path fast (no DB lookup per request)
