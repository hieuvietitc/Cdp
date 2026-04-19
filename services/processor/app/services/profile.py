from sqlalchemy.orm import Session

from cdp_shared.models.profile import Profile
from cdp_shared.models.identity import Identity


class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def update_traits(self, profile: Profile, new_traits: dict) -> None:
        """Merge new_traits into profile.traits. Existing keys preserved unless overwritten."""
        merged = {**profile.traits, **new_traits}

        # Sync top-level identity fields from traits to dedicated columns
        for field in ("email", "phone"):
            if field in new_traits and new_traits[field]:
                current_val = getattr(profile, field)
                if not current_val:
                    setattr(profile, field, new_traits[field])
                    self._ensure_identity(profile, field, new_traits[field])

        profile.traits = merged
        profile.is_anonymous = False
        self.db.commit()

    def _ensure_identity(self, profile: Profile, id_type: str, id_value: str):
        from sqlalchemy import select
        exists = self.db.execute(
            select(Identity).where(Identity.id_type == id_type, Identity.id_value == id_value)
        ).scalar_one_or_none()
        if not exists:
            self.db.add(Identity(
                profile_id=profile.id,
                id_type=id_type,
                id_value=id_value,
                source="identify",
            ))
            self.db.flush()
