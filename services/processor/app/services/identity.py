import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from cdp_shared.models.profile import Profile
from cdp_shared.models.identity import Identity
from cdp_shared.redis_client import get_redis

logger = logging.getLogger(__name__)

ANON_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days


class IdentityResolver:
    """
    Resolves an incoming event to a Profile.

    Priority order:
      1. user_id   → look up identity graph
      2. email/phone in traits (for identify events)
      3. anonymous_id → look up identity graph (or Redis cache)
      4. Create new anonymous profile
    """

    def __init__(self, db: Session):
        self.db = db
        self.redis = get_redis()

    def resolve(self, event_data: dict) -> Profile | None:
        user_id = event_data.get("user_id")
        anonymous_id = event_data.get("anonymous_id")
        traits = event_data.get("traits") or {}
        event_type = event_data.get("event_type", "track")

        known_profile = None

        # ── Step 1: Resolve by user_id ─────────────────────────────────
        if user_id:
            known_profile = self._find_by_identity("loyalty_id", user_id)
            if not known_profile:
                known_profile = self._find_by_identity("user_id", user_id)

        # ── Step 2: Resolve by email / phone (identify events) ─────────
        if not known_profile and event_type == "identify":
            email = traits.get("email")
            phone = traits.get("phone")
            if email:
                known_profile = self._find_profile_by_field("email", email)
            if not known_profile and phone:
                known_profile = self._find_profile_by_field("phone", phone)

        # ── Step 3: Merge anonymous → known ────────────────────────────
        if known_profile and anonymous_id:
            anon_profile = self._get_anonymous_profile(anonymous_id)
            if anon_profile and anon_profile.id != known_profile.id:
                self._merge(anon_profile, known_profile)
            # Cache the resolution
            self.redis.setex(f"cdp:anon:{anonymous_id}", ANON_CACHE_TTL, str(known_profile.id))
            # Register anonymous_id as identity of known profile
            self._ensure_identity(known_profile.id, "anonymous_id", anonymous_id, "web_sdk")
            return known_profile

        if known_profile:
            return known_profile

        # ── Step 4: Resolve / create anonymous profile ──────────────────
        if anonymous_id:
            return self._get_or_create_anonymous(anonymous_id)

        return None

    def _find_by_identity(self, id_type: str, id_value: str) -> Profile | None:
        row = self.db.execute(
            select(Identity).where(
                Identity.id_type == id_type,
                Identity.id_value == id_value,
            )
        ).scalar_one_or_none()
        if row:
            return self.db.get(Profile, row.profile_id)
        return None

    def _find_profile_by_field(self, field: str, value: str) -> Profile | None:
        return self.db.execute(
            select(Profile).where(getattr(Profile, field) == value)
        ).scalar_one_or_none()

    def _get_anonymous_profile(self, anonymous_id: str) -> Profile | None:
        # Check Redis cache first
        cached = self.redis.get(f"cdp:anon:{anonymous_id}")
        if cached:
            return self.db.get(Profile, uuid.UUID(cached))
        return self._find_by_identity("anonymous_id", anonymous_id)

    def _get_or_create_anonymous(self, anonymous_id: str) -> Profile:
        profile = self._get_anonymous_profile(anonymous_id)
        if profile:
            return profile
        profile = Profile(is_anonymous=True, traits={})
        self.db.add(profile)
        self.db.flush()
        identity = Identity(
            profile_id=profile.id,
            id_type="anonymous_id",
            id_value=anonymous_id,
            source="web_sdk",
        )
        self.db.add(identity)
        self.db.commit()
        self.redis.setex(f"cdp:anon:{anonymous_id}", ANON_CACHE_TTL, str(profile.id))
        return profile

    def _ensure_identity(self, profile_id: uuid.UUID, id_type: str, id_value: str, source: str):
        exists = self.db.execute(
            select(Identity).where(Identity.id_type == id_type, Identity.id_value == id_value)
        ).scalar_one_or_none()
        if not exists:
            self.db.add(Identity(profile_id=profile_id, id_type=id_type, id_value=id_value, source=source))
            self.db.commit()

    def _merge(self, source: Profile, target: Profile):
        """Move all identities and events from source → target, then mark source as merged."""
        from cdp_shared.models.event import Event
        self.db.execute(
            Identity.__table__.update()
            .where(Identity.profile_id == source.id)
            .values(profile_id=target.id)
        )
        self.db.execute(
            Event.__table__.update()
            .where(Event.profile_id == source.id)
            .values(profile_id=target.id)
        )
        source.merged_into = target.id
        self.db.commit()
        logger.info("Merged profile %s → %s", source.id, target.id)
