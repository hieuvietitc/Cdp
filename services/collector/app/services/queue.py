import json
from functools import lru_cache

import redis as redis_lib

from cdp_shared.config import settings

MAX_STREAM_LEN = 1_000_000  # approx ~500MB at avg 500 bytes/event


class QueueService:
    def __init__(self):
        self._r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)

    def push(self, stream: str, message: dict) -> str:
        """Push message to Redis Stream, returns entry ID."""
        flat = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) if v is not None else "" for k, v in message.items()}
        return self._r.xadd(stream, flat, maxlen=MAX_STREAM_LEN, approximate=True)

    def ping(self) -> bool:
        try:
            return self._r.ping()
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_queue_service() -> QueueService:
    return QueueService()
