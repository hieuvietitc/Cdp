import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.worker import app
from app.destinations.sendgrid import SendGridDestination
from app.destinations.sms_esms import ESMSDestination
from app.destinations.meta_ads import MetaAdsDestination
from cdp_shared.db import SessionLocal
from cdp_shared.models.activation import Activation, ActivationEvent, Destination
from cdp_shared.models.segment import SegmentMember
from cdp_shared.models.profile import Profile

logger = logging.getLogger(__name__)

DESTINATION_MAP = {
    "sendgrid": SendGridDestination,
    "sms_esms": ESMSDestination,
    "meta_ads": MetaAdsDestination,
}


@app.task(bind=True, max_retries=2, queue="cdp_activations")
def run_activation(self, activation_id: str):
    act_uuid = uuid.UUID(activation_id)
    try:
        with SessionLocal() as db:
            activation = db.get(Activation, act_uuid)
            if not activation:
                logger.warning("Activation %s not found", activation_id)
                return

            dest = db.get(Destination, activation.destination_id)
            if not dest or not dest.is_active:
                activation.status = "failed"
                activation.errors = ["Destination not found or inactive"]
                db.commit()
                return

            dest_cls = DESTINATION_MAP.get(dest.type)
            if not dest_cls:
                activation.status = "failed"
                activation.errors = [f"Unknown destination type: {dest.type}"]
                db.commit()
                return

            # Mark running
            activation.status = "running"
            activation.started_at = datetime.now(timezone.utc)
            db.commit()

            # Fetch segment members with profile data
            rows = db.execute(
                select(Profile)
                .join(SegmentMember, SegmentMember.profile_id == Profile.id)
                .where(SegmentMember.segment_id == activation.segment_id)
                .where(Profile.merged_into.is_(None))
            ).scalars().all()

            profiles = [
                {
                    "id": str(p.id),
                    "email": p.email,
                    "phone": p.phone,
                    "traits": p.traits,
                }
                for p in rows
            ]

            # Execute destination
            destination_instance = dest_cls(dest.config)
            sent_count, errors = destination_instance.send(profiles)

            # Persist per-profile log
            log_entries = []
            for p in rows:
                log_entries.append(ActivationEvent(
                    activation_id=act_uuid,
                    profile_id=p.id,
                    status="sent" if sent_count > 0 else "failed",
                ))
            db.bulk_save_objects(log_entries)

            activation.profiles_sent = sent_count
            activation.errors = errors
            activation.status = "failed" if errors and sent_count == 0 else "completed"
            activation.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info("Activation %s done: %d sent, %d errors", activation_id, sent_count, len(errors))

    except Exception as exc:
        logger.error("run_activation failed: %s", exc, exc_info=True)
        with SessionLocal() as db:
            activation = db.get(Activation, act_uuid)
            if activation:
                activation.status = "failed"
                activation.errors = [str(exc)]
                db.commit()
        raise self.retry(exc=exc)
