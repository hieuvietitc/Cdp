import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, select, delete

from app.worker import app
from cdp_shared.sql_builder import SQLBuilder
from cdp_shared.db import SessionLocal
from cdp_shared.models.segment import Segment, SegmentMember

logger = logging.getLogger(__name__)

# Fetch and insert members in pages — prevents OOM on large segments (500K+)
MEMBER_PAGE_SIZE = 10_000


@app.task(bind=True, max_retries=2, queue="cdp_segments")
def refresh_segment(self, segment_id: str):
    """
    Recompute segment membership using paginated streaming:
    1. Build WHERE clause from rules
    2. DELETE old members
    3. Stream-insert new members in pages of MEMBER_PAGE_SIZE
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

            # Paginated profile lookup — ORDER BY id ensures stable pagination
            find_page_sql = text(
                f"SELECT id FROM cdp.profiles"
                f" WHERE merged_into IS NULL AND ({where_clause})"
                f" ORDER BY id"
                f" LIMIT :_page_size OFFSET :_offset"
            )

            # Clear old membership first
            db.execute(delete(SegmentMember).where(SegmentMember.segment_id == seg_uuid))
            db.flush()

            total = 0
            offset = 0
            while True:
                page_params = {**params, "_page_size": MEMBER_PAGE_SIZE, "_offset": offset}
                rows = db.execute(find_page_sql, page_params).fetchall()
                if not rows:
                    break

                db.execute(
                    SegmentMember.__table__.insert(),
                    [{"segment_id": seg_uuid, "profile_id": r[0]} for r in rows],
                )
                db.flush()
                total += len(rows)
                offset += MEMBER_PAGE_SIZE
                logger.debug("Segment %s: inserted %d members so far", segment_id, total)

                # Short-circuit if last page was smaller than page size
                if len(rows) < MEMBER_PAGE_SIZE:
                    break

            segment.member_count = total
            segment.last_computed = datetime.now(timezone.utc)
            db.commit()

            logger.info("Segment %s refreshed: %d members", segment_id, total)
            return total

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
