import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func

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

# Stream profiles in pages to avoid loading entire segment into memory
PROFILE_PAGE_SIZE = 2_000


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

            destination_instance = dest_cls(dest.config)
            total_sent = 0
            all_errors: list[str] = []

            # Stream profiles in pages — safe for 1M+ member segments
            offset = 0
            while True:
                rows = db.execute(
                    select(Profile)
                    .join(SegmentMember, SegmentMember.profile_id == Profile.id)
                    .where(SegmentMember.segment_id == activation.segment_id)
                    .where(Profile.merged_into.is_(None))
                    .where(Profile.email.is_not(None) | Profile.phone.is_not(None))
                    .order_by(Profile.id)
                    .offset(offset)
                    .limit(PROFILE_PAGE_SIZE)
                ).scalars().all()

                if not rows:
                    break

                profiles = [
                    {"id": str(p.id), "email": p.email, "phone": p.phone, "traits": p.traits}
                    for p in rows
                ]

                page_sent, page_errors = destination_instance.send(profiles)
                total_sent += page_sent
                all_errors.extend(page_errors)

                # Log per-profile status for this page
                log_entries = []
                sent_set = set()  # destinations don't give per-profile feedback; best effort
                for p in rows:
                    # Mark as sent if no errors in this batch; failed otherwise
                    status = "sent" if not page_errors else ("sent" if page_sent == len(profiles) else "failed")
                    log_entries.append(ActivationEvent(
                        activation_id=act_uuid,
                        profile_id=p.id,
                        status=status,
                        error_message=page_errors[0] if page_errors and status == "failed" else None,
                    ))
                db.bulk_save_objects(log_entries)
                db.flush()

                offset += PROFILE_PAGE_SIZE

            activation.profiles_sent = total_sent
            activation.errors = all_errors[:50]  # cap stored error list at 50 entries
            if all_errors and total_sent == 0:
                activation.status = "failed"
            elif all_errors:
                activation.status = "completed_with_errors"
            else:
                activation.status = "completed"
            activation.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                "Activation %s done: %d sent, %d errors",
                activation_id, total_sent, len(all_errors),
            )

    except Exception as exc:
        logger.error("run_activation failed: %s", exc, exc_info=True)
        with SessionLocal() as db:
            activation = db.get(Activation, act_uuid)
            if activation:
                activation.status = "failed"
                activation.errors = [str(exc)]
                db.commit()
        raise self.retry(exc=exc)
