import logging
from datetime import datetime, timezone

from app.worker import app
from app.services.identity import IdentityResolver
from app.services.profile import ProfileService
from cdp_shared.db import SessionLocal
from cdp_shared.models.event import Event

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=5, queue="cdp_events")
def process_event(self, event_data: dict):
    """Main event processing pipeline: identity resolution → profile update → event persist."""
    try:
        with SessionLocal() as db:
            event_type = event_data.get("event_type", "track")

            # 1. Resolve identity
            resolver = IdentityResolver(db)
            profile = resolver.resolve(event_data)

            # 2. Handle identify call: update traits
            if event_type == "identify":
                traits = event_data.get("traits") or {}
                if traits and profile:
                    svc = ProfileService(db)
                    svc.update_traits(profile, traits)

            # 3. Persist event
            occurred_at = _parse_timestamp(event_data.get("timestamp") or event_data.get("received_at"))
            ev = Event(
                profile_id=profile.id if profile else None,
                anonymous_id=event_data.get("anonymous_id"),
                session_id=event_data.get("session_id"),
                event_type=event_type,
                event_name=event_data.get("event") or event_type,
                properties=event_data.get("properties") or {},
                context=event_data.get("context") or {},
                source=_detect_source(event_data),
                occurred_at=occurred_at,
            )
            db.add(ev)
            db.commit()

    except Exception as exc:
        logger.error("process_event failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


def _parse_timestamp(ts) -> datetime:
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _detect_source(event_data: dict) -> str:
    ctx = event_data.get("context") or {}
    sdk = ctx.get("sdk_version", "")
    if sdk:
        return "web_sdk"
    return event_data.get("source", "web_sdk")
