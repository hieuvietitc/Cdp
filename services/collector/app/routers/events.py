import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from cdp_shared.schemas.event import TrackEventIn, IdentifyEventIn, PageEventIn, BatchEventIn
from app.middleware.auth import validate_write_key
from app.services.queue import QueueService, get_queue_service

router = APIRouter()

STREAM_NAME = "cdp:events:raw"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/events")
async def track_event(
    payload: TrackEventIn,
    request: Request,
    qs: QueueService = Depends(get_queue_service),
):
    validate_write_key(payload.write_key)
    _enrich_context(payload.context, request)
    message = payload.model_dump(mode="json")
    message["received_at"] = _now_iso()
    message["event_type"] = "track"
    qs.push(STREAM_NAME, message)
    return {"status": "queued"}


@router.post("/identify")
async def identify(
    payload: IdentifyEventIn,
    request: Request,
    qs: QueueService = Depends(get_queue_service),
):
    validate_write_key(payload.write_key)
    _enrich_context(payload.context, request)
    message = payload.model_dump(mode="json")
    message["received_at"] = _now_iso()
    message["event_type"] = "identify"
    message["event"] = "Identify"
    qs.push(STREAM_NAME, message)
    return {"status": "queued"}


@router.post("/page")
async def page_view(
    payload: PageEventIn,
    request: Request,
    qs: QueueService = Depends(get_queue_service),
):
    validate_write_key(payload.write_key)
    _enrich_context(payload.context, request)
    message = payload.model_dump(mode="json")
    message["received_at"] = _now_iso()
    message["event_type"] = "page"
    message["event"] = "Page View"
    qs.push(STREAM_NAME, message)
    return {"status": "queued"}


@router.post("/events/batch")
async def batch_events(
    payload: BatchEventIn,
    request: Request,
    qs: QueueService = Depends(get_queue_service),
):
    validate_write_key(payload.write_key)
    accepted = 0
    rejected = 0
    for item in payload.batch:
        try:
            _enrich_context(item.context, request)
            message = item.model_dump(mode="json")
            message["received_at"] = _now_iso()
            qs.push(STREAM_NAME, message)
            accepted += 1
        except Exception:
            rejected += 1
    return {"accepted": accepted, "rejected": rejected}


def _enrich_context(context, request: Request) -> None:
    """Add server-side IP if not present."""
    if not getattr(context, "ip", None):
        context.ip = request.client.host if request.client else None
