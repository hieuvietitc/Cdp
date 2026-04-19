import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, UUID, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cdp_shared.db import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_profile", "profile_id", "occurred_at"),
        Index("idx_events_anon", "anonymous_id", "occurred_at"),
        Index("idx_events_type", "event_type", "occurred_at"),
        {"schema": "cdp", "postgresql_partition_by": "RANGE (occurred_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.profiles.id"), nullable=True
    )
    anonymous_id: Mapped[str | None] = mapped_column(String, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # page_view | product_click | search | booking_started | booking_completed
    # payment_completed | identify | loyalty_earned | email_opened
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_name: Mapped[str] = mapped_column(String, nullable=False)

    properties: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # web_sdk | mobile_sdk | batch_sales | batch_loyalty | webhook
    source: Mapped[str] = mapped_column(String, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    profile: Mapped["Profile | None"] = relationship(back_populates="events")  # noqa: F821
