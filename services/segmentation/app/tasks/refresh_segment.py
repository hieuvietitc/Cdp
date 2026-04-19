import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, select, delete

from app.worker import app
from app.engine.sql_builder import SQLBuilder
from cdp_shared.db import SessionLocal
from cdp_shared.models.segment import Segment, SegmentMember

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=2, queue="cdp_segments")
def refresh_segment(self, segment_id: str):
    """
    Recompute segment membership:
    1. Build WHERE clause from rules
    2. DELETE old members
    3. INSERT new members from query
    4. Update member_count + last_computed
    """
    try:
        seg_uuid = uuid.UUID(segment_id)
        with SessionLocal() as db:
            segment = db.get(Segment, seg_uuid)
            if not segment:
                logger.warning("Segment %s not found", segment_id)
                return

            builder = SQLBuilder()
            where_clause, params = builder.build(segment.rules)

            find_members_sql = f"""
                SELECT id FROM cdp.profiles
                WHERE merged_into IS NULL
                AND ({where_clause})
            """

            rows = db.execute(text(find_members_sql), params).fetchall()
            profile_ids = [r[0] for r in rows]

            # Atomically replace membership
            db.execute(
                delete(SegmentMember).where(SegmentMember.segment_id == seg_uuid)
            )
            if profile_ids:
                db.execute(
                    SegmentMember.__table__.insert(),
                    [{"segment_id": seg_uuid, "profile_id": pid} for pid in profile_ids],
                )

            segment.member_count = len(profile_ids)
            segment.last_computed = datetime.now(timezone.utc)
            db.commit()

            logger.info("Segment %s refreshed: %d members", segment_id, len(profile_ids))
            return len(profile_ids)

    except Exception as exc:
        logger.error("refresh_segment failed for %s: %s", segment_id, exc, exc_info=True)
        raise self.retry(exc=exc)


@app.task(queue="cdp_segments")
def refresh_all_scheduled_segments():
    """Called by Celery beat to trigger refresh for all scheduled segments."""
    with SessionLocal() as db:
        segments = db.execute(
            select(Segment).where(Segment.refresh_mode == "scheduled")
        ).scalars().all()
        for seg in segments:
            refresh_segment.apply_async(args=[str(seg.id)], queue="cdp_segments")
        logger.info("Queued refresh for %d scheduled segments", len(segments))
