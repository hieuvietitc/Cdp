import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from cdp_shared.db import SessionLocal
from cdp_shared.models.profile import Profile
from cdp_shared.models.identity import Identity
from cdp_shared.models.event import Event

logger = logging.getLogger(__name__)


class ProfileLoader:
    """Upserts profiles and events from batch connectors into the CDP database."""

    def upsert_loyalty_batch(self, records: list[dict]) -> None:
        with SessionLocal() as db:
            for rec in records:
                try:
                    profile = self._find_or_create_profile(db, rec)
                    # Merge traits
                    merged_traits = {**profile.traits, **rec.get("traits", {})}
                    profile.traits = merged_traits
                    profile.is_anonymous = False
                    if rec.get("email") and not profile.email:
                        profile.email = rec["email"]
                    if rec.get("phone") and not profile.phone:
                        profile.phone = rec["phone"]
                    if rec.get("loyalty_member_id") and not profile.loyalty_member_id:
                        profile.loyalty_member_id = rec["loyalty_member_id"]
                    self._ensure_identities(db, profile, rec)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error("Failed to upsert loyalty record: %s", e)

    def upsert_booking_events(self, records: list[dict]) -> None:
        with SessionLocal() as db:
            for rec in records:
                try:
                    profile = self._find_or_create_profile(db, rec)
                    if rec.get("sales_customer_id") and not profile.sales_customer_id:
                        profile.sales_customer_id = rec["sales_customer_id"]

                    evt_data = rec.get("event", {})
                    booking_id = evt_data.get("properties", {}).get("booking_id")

                    # Skip duplicate events (idempotency)
                    if booking_id:
                        existing = db.execute(
                            select(Event).where(
                                Event.profile_id == profile.id,
                                Event.event_type == "booking_completed",
                                Event.properties["booking_id"].astext == booking_id,
                            )
                        ).scalar_one_or_none()
                        if existing:
                            continue

                    occurred_at = evt_data.get("occurred_at")
                    if isinstance(occurred_at, str):
                        occurred_at = datetime.fromisoformat(str(occurred_at).replace("Z", "+00:00"))
                    elif not isinstance(occurred_at, datetime):
                        occurred_at = datetime.now(timezone.utc)

                    event = Event(
                        profile_id=profile.id,
                        event_type=evt_data.get("event_type", "booking_completed"),
                        event_name=evt_data.get("event_name", "Booking Completed"),
                        properties=evt_data.get("properties", {}),
                        context={},
                        source=evt_data.get("source", "batch_sales"),
                        occurred_at=occurred_at,
                    )
                    db.add(event)
                    self._ensure_identities(db, profile, rec)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error("Failed to upsert booking event: %s", e)

    def _find_or_create_profile(self, db, rec: dict) -> Profile:
        profile = None

        # Try finding by identity fields (priority: loyalty_id > email > phone > sales_id)
        for id_type, field in [
            ("loyalty_id", "loyalty_member_id"),
            ("email", "email"),
            ("phone", "phone"),
            ("sales_customer_id", "sales_customer_id"),
        ]:
            val = rec.get(field) or rec.get(id_type)
            if not val:
                continue
            if field in ("email", "phone", "loyalty_member_id", "sales_customer_id"):
                profile = db.execute(
                    select(Profile).where(getattr(Profile, field) == val)
                ).scalar_one_or_none()
            if profile:
                break

        if not profile:
            profile = Profile(is_anonymous=False, traits={})
            db.add(profile)
            db.flush()

        return profile

    def _ensure_identities(self, db, profile: Profile, rec: dict):
        for id_type, field in [
            ("loyalty_id", "loyalty_member_id"),
            ("email", "email"),
            ("phone", "phone"),
            ("sales_customer_id", "sales_customer_id"),
        ]:
            val = rec.get(field)
            if not val:
                continue
            exists = db.execute(
                select(Identity).where(Identity.id_type == id_type, Identity.id_value == val)
            ).scalar_one_or_none()
            if not exists:
                db.add(Identity(
                    profile_id=profile.id,
                    id_type=id_type,
                    id_value=val,
                    source=rec.get("source", "batch"),
                ))
        db.flush()
