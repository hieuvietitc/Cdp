import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, UUID, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cdp_shared.db import Base


class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # sendgrid | sms_esms | meta_ads | google_ads | webhook
    type: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activations: Mapped[list["Activation"]] = relationship(back_populates="destination")


class Activation(Base):
    __tablename__ = "activations"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.segments.id"), nullable=False
    )
    destination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.destinations.id"), nullable=False
    )
    # manual | scheduled | realtime
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    profiles_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    destination: Mapped["Destination"] = relationship(back_populates="activations")
    events: Mapped[list["ActivationEvent"]] = relationship(back_populates="activation")


class ActivationEvent(Base):
    __tablename__ = "activation_events"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.activations.id"), nullable=False
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.profiles.id"), nullable=False
    )
    # sent | failed | skipped
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    activation: Mapped["Activation"] = relationship(back_populates="events")
