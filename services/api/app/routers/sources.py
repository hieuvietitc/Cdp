import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.source import Source
from cdp_shared.models.event import Event
from cdp_shared.redis_client import get_redis
from app.auth.jwt import get_current_user

router = APIRouter()

# Map Source.type → Event.source string stored by processor
_SOURCE_TYPE_MAP = {
    "web": "web_sdk",
    "ios": "mobile_sdk",
    "android": "mobile_sdk",
    "server": "server_side",
}


class SourceCreate(BaseModel):
    name: str
    type: str  # web | ios | android | server


def _serialize(s: Source) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "type": s.type,
        "write_key": s.write_key,
        "is_active": s.is_active,
        "created_at": s.created_at,
    }


@router.get("")
def list_sources(db: Session = Depends(get_db), _=Depends(get_current_user)):
    sources = db.execute(select(Source)).scalars().all()
    return [_serialize(s) for s in sources]


@router.post("", status_code=201)
def create_source(body: SourceCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    write_key = "wk_" + secrets.token_hex(24)
    source = Source(name=body.name, type=body.type, write_key=write_key)
    db.add(source)
    db.commit()
    get_redis().setex(f"cdp:write_key:{write_key}", 86400, "1")
    return _serialize(source)


@router.get("/{source_id}")
def get_source(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _serialize(source)


@router.get("/{source_id}/stats")
def source_stats(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    event_source = _SOURCE_TYPE_MAP.get(source.type, source.type)

    # Events per day — last 30 days
    daily_sql = text("""
        SELECT DATE_TRUNC('day', occurred_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AS day,
               COUNT(*) AS events
        FROM cdp.events
        WHERE source = :src
          AND occurred_at >= NOW() - (INTERVAL '1 day' * 30)
        GROUP BY 1
        ORDER BY 1
    """)
    daily = [
        {"day": str(row.day), "events": row.events}
        for row in db.execute(daily_sql, {"src": event_source})
    ]

    # Top event types — last 30 days
    types_sql = text("""
        SELECT event_name, COUNT(*) AS cnt
        FROM cdp.events
        WHERE source = :src
          AND occurred_at >= NOW() - (INTERVAL '1 day' * 30)
        GROUP BY event_name
        ORDER BY cnt DESC
        LIMIT 10
    """)
    top_types = [
        {"event_name": row.event_name, "count": row.cnt}
        for row in db.execute(types_sql, {"src": event_source})
    ]

    # Total events all-time for this source
    total = db.execute(
        select(func.count()).select_from(Event).where(Event.source == event_source)
    ).scalar()

    return {
        "source_id": str(source_id),
        "event_source": event_source,
        "total_events": total,
        "daily": daily,
        "top_event_types": top_types,
    }


@router.post("/{source_id}/rotate-key")
def rotate_key(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    old_key = source.write_key
    new_key = "wk_" + secrets.token_hex(24)
    source.write_key = new_key
    db.commit()
    r = get_redis()
    r.delete(f"cdp:write_key:{old_key}")
    r.setex(f"cdp:write_key:{new_key}", 86400, "1")
    return {"write_key": new_key}


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = False
    db.commit()

