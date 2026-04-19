import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.profile import Profile
from cdp_shared.models.event import Event
from cdp_shared.models.segment import SegmentMember, Segment
from cdp_shared.schemas.profile import ProfileOut, ProfileDetail, PaginatedProfiles
from app.auth.jwt import get_current_user

router = APIRouter()


@router.get("", response_model=PaginatedProfiles)
def list_profiles(
    q: Optional[str] = Query(None, description="email:foo@bar.com | phone:+849 | loyalty_id:123"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Profile).where(Profile.merged_into.is_(None))

    if q:
        key, _, val = q.partition(":")
        val = val.strip()
        if key == "email":
            stmt = stmt.where(Profile.email.ilike(f"%{val}%"))
        elif key == "phone":
            stmt = stmt.where(Profile.phone.ilike(f"%{val}%"))
        elif key in ("loyalty_id", "loyalty_member_id"):
            stmt = stmt.where(Profile.loyalty_member_id == val)
        elif key == "sales_customer_id":
            stmt = stmt.where(Profile.sales_customer_id == val)
        else:
            stmt = stmt.where(
                or_(
                    Profile.email.ilike(f"%{q}%"),
                    Profile.phone.ilike(f"%{q}%"),
                )
            )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = db.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()
    return PaginatedProfiles(items=items, total=total, page=page, size=size)


@router.get("/{profile_id}", response_model=ProfileDetail)
def get_profile(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/{profile_id}/events")
def get_profile_events(
    profile_id: uuid.UUID,
    event_type: Optional[str] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Event).where(Event.profile_id == profile_id).order_by(Event.occurred_at.desc())
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    events = db.execute(stmt.limit(limit)).scalars().all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "event_name": e.event_name,
            "properties": e.properties,
            "source": e.source,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in events
    ]


@router.get("/{profile_id}/segments")
def get_profile_segments(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = db.execute(
        select(Segment)
        .join(SegmentMember, SegmentMember.segment_id == Segment.id)
        .where(SegmentMember.profile_id == profile_id)
    ).scalars().all()
    return [{"id": str(s.id), "name": s.name, "member_count": s.member_count} for s in rows]


@router.post("/{profile_id}/merge")
def merge_profiles(
    profile_id: uuid.UUID,
    body: dict,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    merge_with = uuid.UUID(body["merge_with_profile_id"])
    source = db.get(Profile, profile_id)
    target = db.get(Profile, merge_with)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Profile not found")
    source.merged_into = target.id
    db.commit()
    return {"merged": str(profile_id), "into": str(merge_with)}
