"""
Connector for the Loyalty system PostgreSQL database.

Reads member profiles incrementally using a watermark stored in Redis.
Adapt the SQL queries to match your loyalty system's actual schema.
"""
import json
import logging
from datetime import datetime, timezone

import redis as redis_lib

from cdp_shared.config import settings
from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

WATERMARK_KEY = "cdp:ingestion:loyalty:watermark"

# ─── ADAPT THESE to match your loyalty DB schema ──────────────────────────
MEMBERS_QUERY = """
    SELECT
        m.member_id,
        m.full_name,
        m.email,
        m.phone,
        m.gender,
        m.date_of_birth,
        m.tier,
        m.points_balance,
        m.total_spend,
        m.join_date,
        m.updated_at
    FROM members m
    WHERE m.updated_at > :watermark
    ORDER BY m.updated_at ASC
"""


class LoyaltyConnector(BaseConnector):
    def __init__(self):
        super().__init__(settings.loyalty_db_url)
        self._redis = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)

    def fetch_members(self):
        watermark = self._get_watermark()
        logger.info("Loyalty sync from watermark: %s", watermark)
        with self.Session() as session:
            for batch in self._fetch_batched(session, MEMBERS_QUERY, {"watermark": watermark}):
                if batch:
                    self._advance_watermark(batch[-1]["updated_at"])
                yield [self._transform(row) for row in batch]

    def _transform(self, row: dict) -> dict:
        """Map loyalty schema → CDP profile dict."""
        phone = row.get("phone") or ""
        # Normalise to E.164 (+84...)
        if phone and not phone.startswith("+"):
            phone = "+84" + phone.lstrip("0")

        return {
            "loyalty_member_id": str(row["member_id"]),
            "email": (row.get("email") or "").strip().lower() or None,
            "phone": phone or None,
            "traits": {
                "full_name": row.get("full_name"),
                "gender": row.get("gender"),
                "dob": str(row["date_of_birth"]) if row.get("date_of_birth") else None,
                "tier": row.get("tier"),
                "loyalty_points": row.get("points_balance"),
                "total_spend_vnd": float(row["total_spend"]) if row.get("total_spend") else None,
                "loyalty_join_date": str(row["join_date"]) if row.get("join_date") else None,
            },
            "source": "loyalty_batch",
        }

    def _get_watermark(self) -> datetime:
        val = self._redis.get(WATERMARK_KEY)
        if val:
            return datetime.fromisoformat(val)
        return datetime(2000, 1, 1, tzinfo=timezone.utc)

    def _advance_watermark(self, new_ts):
        if isinstance(new_ts, datetime):
            self._redis.set(WATERMARK_KEY, new_ts.isoformat())
        elif new_ts:
            self._redis.set(WATERMARK_KEY, str(new_ts))
