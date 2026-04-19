"""
Connector for the Sales/Booking system PostgreSQL database.

Reads booking transactions incrementally.
Adapt the SQL queries to match your sales system's actual schema.
"""
import logging
from datetime import datetime, timezone

import redis as redis_lib

from cdp_shared.config import settings
from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)

WATERMARK_KEY = "cdp:ingestion:sales:watermark"

# ─── ADAPT THESE to match your sales DB schema ────────────────────────────
BOOKINGS_QUERY = """
    SELECT
        b.booking_id,
        b.customer_id,
        b.customer_email,
        b.customer_phone,
        b.tour_code,
        b.tour_name,
        b.destination,
        b.departure_date,
        b.return_date,
        b.adults,
        b.children,
        b.total_price,
        b.payment_method,
        b.booking_status,
        b.booking_date,
        b.updated_at
    FROM bookings b
    WHERE b.updated_at > :watermark
    ORDER BY b.updated_at ASC
"""


class SalesConnector(BaseConnector):
    def __init__(self):
        super().__init__(settings.sales_db_url)
        self._redis = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)

    def fetch_bookings(self):
        watermark = self._get_watermark()
        logger.info("Sales sync from watermark: %s", watermark)
        with self.Session() as session:
            for batch in self._fetch_batched(session, BOOKINGS_QUERY, {"watermark": watermark}):
                if batch:
                    self._advance_watermark(batch[-1]["updated_at"])
                yield [self._transform(row) for row in batch]

    def _transform(self, row: dict) -> dict:
        """Map booking row → CDP event + profile hint."""
        phone = row.get("customer_phone") or ""
        if phone and not phone.startswith("+"):
            phone = "+84" + phone.lstrip("0")

        return {
            "sales_customer_id": str(row["customer_id"]),
            "email": (row.get("customer_email") or "").strip().lower() or None,
            "phone": phone or None,
            "event": {
                "event_type": "booking_completed",
                "event_name": "Booking Completed",
                "properties": {
                    "booking_id": str(row["booking_id"]),
                    "tour_code": row.get("tour_code"),
                    "tour_name": row.get("tour_name"),
                    "destination": row.get("destination"),
                    "departure_date": str(row["departure_date"]) if row.get("departure_date") else None,
                    "return_date": str(row["return_date"]) if row.get("return_date") else None,
                    "adults": row.get("adults"),
                    "children": row.get("children"),
                    "total_price_vnd": float(row["total_price"]) if row.get("total_price") else None,
                    "payment_method": row.get("payment_method"),
                    "booking_status": row.get("booking_status"),
                },
                "occurred_at": row.get("booking_date") or row.get("updated_at"),
                "source": "batch_sales",
            },
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
