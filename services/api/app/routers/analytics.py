from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from app.auth.jwt import get_current_user

router = APIRouter()


@router.get("/events/timeseries")
def events_timeseries(
    event_type: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    # INTERVAL '1 day' * :days is the correct way to parameterize an interval
    sql = text("""
        SELECT DATE_TRUNC('day', occurred_at) AS day, COUNT(*) AS cnt
        FROM cdp.events
        WHERE event_type = :event_type
          AND occurred_at >= NOW() - (INTERVAL '1 day' * :days)
        GROUP BY 1 ORDER BY 1
    """)
    rows = db.execute(sql, {"event_type": event_type, "days": days}).mappings().all()
    return [{"day": str(r["day"].date()), "count": r["cnt"]} for r in rows]


@router.get("/profiles/growth")
def profile_growth(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    sql = text("""
        SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*) AS new_profiles
        FROM cdp.profiles
        WHERE created_at >= NOW() - (INTERVAL '1 day' * :days)
          AND is_anonymous = false
        GROUP BY 1 ORDER BY 1
    """)
    rows = db.execute(sql, {"days": days}).mappings().all()
    return [{"day": str(r["day"].date()), "new_profiles": r["new_profiles"]} for r in rows]


@router.get("/funnel")
def funnel_analysis(
    events: str = Query(..., description="Comma-separated event types: page_view,booking_started,booking_completed"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    import re
    event_list = [e.strip() for e in events.split(",")]
    # Validate each event type against safe identifier pattern
    safe_re = re.compile(r"^[A-Za-z0-9_]{1,100}$")
    for ev in event_list:
        if not safe_re.match(ev):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Invalid event type: '{ev}'")

    results = []
    for ev in event_list:
        row = db.execute(
            text("""
                SELECT COUNT(DISTINCT profile_id) AS users
                FROM cdp.events
                WHERE event_type = :ev
                  AND occurred_at >= NOW() - (INTERVAL '1 day' * :days)
                  AND profile_id IS NOT NULL
            """),
            {"ev": ev, "days": days},
        ).scalar_one()
        results.append({"step": ev, "users": row})
    return results


@router.get("/top_destinations")
def top_destinations(
    days: int = Query(90, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    # limit is int-validated (ge=1, le=50), safe to interpolate
    safe_limit = min(int(limit), 50)
    sql = text(f"""
        SELECT properties->>'destination' AS destination, COUNT(*) AS bookings
        FROM cdp.events
        WHERE event_type = 'booking_completed'
          AND occurred_at >= NOW() - (INTERVAL '1 day' * :days)
          AND properties->>'destination' IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC LIMIT {safe_limit}
    """)
    rows = db.execute(sql, {"days": days}).mappings().all()
    return [{"destination": r["destination"], "bookings": r["bookings"]} for r in rows]
