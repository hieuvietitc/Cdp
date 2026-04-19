import json
import logging
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

STREAM_NAME = "cdp:events:raw"
CONSUMER_GROUP = "cdp_processor"
CONSUMER_NAME = "worker_1"

logger = logging.getLogger(__name__)


def start_stream_consumer():
    """Run Redis Streams consumer in a background thread, dispatching Celery tasks."""
    r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
    # Create consumer group if it doesn't exist
    try:
        r.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except redis_lib.exceptions.ResponseError:
        pass  # group already exists

    logger.info("Stream consumer started on %s", STREAM_NAME)
    while True:
        try:
            results = r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_NAME: ">"},
                count=50,
                block=2000,
            )
            if not results:
                continue
            for _stream, messages in results:
                for msg_id, fields in messages:
                    try:
                        _dispatch(fields)
                        r.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
                    except Exception as e:
                        logger.error("Failed to dispatch msg %s: %s", msg_id, e)
        except Exception as e:
            logger.error("Stream consumer error: %s", e)
            time.sleep(5)


def _dispatch(fields: dict):
    from app.tasks.ingest_event import process_event
    # Deserialise JSON-encoded nested fields
    event_data = {}
    for k, v in fields.items():
        try:
            event_data[k] = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            event_data[k] = v
    process_event.apply_async(args=[event_data], queue="cdp_events")


# Auto-start stream consumer when worker boots
@app.on_after_configure.connect
def setup_stream_consumer(sender, **kwargs):
    t = threading.Thread(target=start_stream_consumer, daemon=True)
    t.start()
