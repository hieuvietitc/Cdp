import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.segment import Segment, SegmentMember
from cdp_shared.models.profile import Profile
from cdp_shared.schemas.segment import SegmentCreate, SegmentUpdate, SegmentOut
from app.auth.jwt import get_current_user

router = APIRouter()


@router.get("", response_model=list[SegmentOut])
def list_segments(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.execute(select(Segment).order_by(Segment.created_at.desc())).scalars().all()


@router.post("", response_model=SegmentOut, status_code=201)
def create_segment(
    body: SegmentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    seg = Segment(
        name=body.name,
        description=body.description,
        rules=body.rules.model_dump(),
        refresh_mode=body.refresh_mode,
        refresh_cron=body.refresh_cron,
        created_by=user.id,
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg


@router.get("/{segment_id}", response_model=SegmentOut)
def get_segment(segment_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    return seg


@router.put("/{segment_id}", response_model=SegmentOut)
def update_segment(
    segment_id: uuid.UUID,
    body: SegmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    if body.name is not None:
        seg.name = body.name
    if body.description is not None:
        seg.description = body.description
    if body.rules is not None:
        seg.rules = body.rules.model_dump()
    if body.refresh_mode is not None:
        seg.refresh_mode = body.refresh_mode
    if body.refresh_cron is not None:
        seg.refresh_cron = body.refresh_cron
    db.commit()
    db.refresh(seg)
    return seg


@router.delete("/{segment_id}", status_code=204)
def delete_segment(segment_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    db.delete(seg)
    db.commit()


@router.post("/{segment_id}/compute")
def trigger_compute(segment_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    from celery import Celery
    from cdp_shared.config import settings
    celery_app = Celery(broker=settings.celery_broker_url)
    celery_app.send_task("app.tasks.refresh_segment.refresh_segment", args=[str(segment_id)], queue="cdp_segments")
    return {"status": "queued", "segment_id": str(segment_id)}


@router.get("/{segment_id}/members")
def get_segment_members(
    segment_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    total = db.execute(
        select(func.count()).where(SegmentMember.segment_id == segment_id)
    ).scalar_one()
    rows = db.execute(
        select(Profile)
        .join(SegmentMember, SegmentMember.profile_id == Profile.id)
        .where(SegmentMember.segment_id == segment_id)
        .offset((page - 1) * size).limit(size)
    ).scalars().all()
    return {
        "total": total,
        "page": page,
        "items": [{"id": str(p.id), "email": p.email, "phone": p.phone, "traits": p.traits} for p in rows],
    }


@router.get("/{segment_id}/preview")
def preview_segment(
    segment_id: uuid.UUID,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Evaluate segment rules and return sample profiles WITHOUT persisting membership."""
    from sqlalchemy import text
    from services.segmentation.app.engine.sql_builder import SQLBuilder  # import from segmentation service
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")
    try:
        builder = SQLBuilder()
        where_clause, params = builder.build(seg.rules)
        rows = db.execute(
            text(f"SELECT id, email, phone, traits FROM cdp.profiles WHERE merged_into IS NULL AND ({where_clause}) LIMIT {limit}"),
            params,
        ).mappings().all()
        return {"count_estimate": len(rows), "sample": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rule evaluation error: {e}")
