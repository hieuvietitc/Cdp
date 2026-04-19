"""
CDP Metrics Exporter — exposes Prometheus metrics not covered by standard exporters:
  - cdp_stream_pending_events      : Redis Stream backlog (event lag)
  - cdp_profiles_total             : total profiles in DB
  - cdp_celery_queue_length{queue} : Celery queue depth
  - cdp_segments_total             : active segment count
"""
import os
import logging
from functools import lru_cache

import redis as redis_lib
from fastapi import FastAPI, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

app = FastAPI(title="CDP Metrics Exporter", docs_url=None)

# ── Prometheus gauges ──────────────────────────────────────────────────────
stream_lag = Gauge("cdp_stream_pending_events", "Events pending in Redis event stream")
profiles_total = Gauge("cdp_profiles_total", "Total CDP profiles")
segments_total = Gauge("cdp_segments_total", "Total active segments")
celery_queue_len = Gauge("cdp_celery_queue_length", "Celery queue depth", ["queue"])


@lru_cache(maxsize=1)
def _redis():
    return redis_lib.from_url(os.environ["REDIS_URL"], decode_responses=True)


@lru_cache(maxsize=1)
def _engine():
    return create_engine(os.environ["DATABASE_URL"], pool_size=2, max_overflow=3)


def _collect():
    r = _redis()

    # Redis Stream lag: pending messages in consumer group
    try:
        groups = r.xinfo_groups("cdp:events")
        pending = sum(g.get("pending", 0) for g in groups)
        stream_lag.set(pending)
    except Exception:
        stream_lag.set(r.xlen("cdp:events"))

    # Celery queue depths (simple Redis list length)
    for queue in ("cdp_events", "cdp_segments", "cdp_activations"):
        try:
            length = r.llen(queue)
            celery_queue_len.labels(queue=queue).set(length)
        except Exception:
            celery_queue_len.labels(queue=queue).set(0)

    # DB stats
    try:
        engine = _engine()
        with engine.connect() as conn:
            profiles_total.set(
                conn.execute(text("SELECT COUNT(*) FROM cdp.profiles WHERE merged_into IS NULL")).scalar()
            )
            segments_total.set(
                conn.execute(text("SELECT COUNT(*) FROM cdp.segments WHERE is_active = true")).scalar()
            )
    except Exception as exc:
        logger.warning("DB metrics collection failed: %s", exc)


@app.get("/metrics")
def metrics():
    _collect()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok"}
