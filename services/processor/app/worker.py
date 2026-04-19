import json
import logging
import os
import socket
import threading
import time

import redis as redis_lib
from celery import Celery

from cdp_shared.config import settings

app = Celery("cdp_processor", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
app.conf.task_routes = {
    "app.tasks.ingest_event.*": {"queue": "cdp_events"},
    "app.tasks.segment_refresh.*": {"queue": "cdp_segments"},
}
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.timezone = "Asia/Ho_Chi_Minh"
# Acknowledge task only after successful execution (not on receipt)
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1  # fair dispatch under load

STREAM_NAME = "cdp:events:raw"
CONSUMER_GROUP = "cdp_processor"
# Unique consumer name per container instance — safe for horizontal scaling
# Use hostname (Docker sets this per container) + thread id
CONSUMER_NAME = f"{socket.gethostname()}-{os.getpid()}"

# How many stream messages to pull per xreadgroup call.
# Tune via env: lower value = lower latency, higher = better throughput
STREAM_BATCH_SIZE = int(os.environ.get("STREAM_BATCH_SIZE", "100"))
# Max lag before we log a warning (useful for capacity alerting)
STREAM_LAG_WARN_THRESHOLD = int(os.environ.get("STREAM_LAG_WARN", "10000"))

logger = logging.getLogger(__name__)


def start_stream_consumer():
    """
    Redis Streams consumer running in a background thread.
    Each processor container has exactly one stream consumer thread;
    add more containers to scale horizontally.
    """
    r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except redis_lib.exceptions.ResponseError:
        pass  # group already exists — expected on restart

    logger.info("Stream consumer started: group=%s consumer=%s", CONSUMER_GROUP, CONSUMER_NAME)

    lag_counter = 0
    while True:
        try:
            results = r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_NAME: ">"},
                count=STREAM_BATCH_SIZE,
                block=2000,  # ms; yields CPU when stream is idle
            )
            if not results:
                lag_counter = 0
                continue

            for _stream, messages in results:
                lag_counter += len(messages)
                for msg_id, fields in messages:
                    try:
                        _dispatch(fields)
                        r.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
                    except Exception as e:
                        logger.error("Dispatch failed for msg %s: %s", msg_id, e)
                        # Do NOT ack — message stays in PEL for retry/inspection

            if lag_counter > STREAM_LAG_WARN_THRESHOLD:
                logger.warning(
                    "Stream consumer lag: processed %d messages without idle. "
                    "Consider adding more processor instances.",
                    lag_counter,
                )
                lag_counter = 0

        except redis_lib.exceptions.ConnectionError as e:
            logger.error("Redis connection lost: %s — retrying in 5s", e)
            time.sleep(5)
        except Exception as e:
            logger.exception("Stream consumer unexpected error: %s", e)
            time.sleep(2)


def _dispatch(fields: dict):
    from app.tasks.ingest_event import process_event
    event_data = {}
    for k, v in fields.items():
        try:
            event_data[k] = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            event_data[k] = v if v != "" else None
    process_event.apply_async(args=[event_data], queue="cdp_events")


@app.on_after_configure.connect
def setup_stream_consumer(sender, **kwargs):
    t = threading.Thread(target=start_stream_consumer, daemon=True, name="stream-consumer")
    t.start()
