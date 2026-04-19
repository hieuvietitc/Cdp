"""Singleton Celery client for the Admin API — used only to send tasks, not to define them."""
from functools import lru_cache

from celery import Celery

from cdp_shared.config import settings


@lru_cache(maxsize=1)
def get_celery() -> Celery:
    client = Celery(broker=settings.celery_broker_url)
    client.conf.task_serializer = "json"
    return client
