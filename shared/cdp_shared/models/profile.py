import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, UUID, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cdp_shared.db import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identity anchors
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    loyalty_member_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    sales_customer_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

    # Dynamic traits: tier, LTV, preferred_destinations, etc.
    traits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    merged_into: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.profiles.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    identities: Mapped[list["Identity"]] = relationship(back_populates="profile")  # noqa: F821
    events: Mapped[list["Event"]] = relationship(back_populates="profile")  # noqa: F821
    segment_memberships: Mapped[list["SegmentMember"]] = relationship(back_populates="profile")  # noqa: F821
