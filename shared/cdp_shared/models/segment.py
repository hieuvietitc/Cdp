import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, UUID, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cdp_shared.db import Base


class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON rule AST: {"operator": "AND", "conditions": [...]}
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # scheduled | realtime
    refresh_mode: Mapped[str] = mapped_column(String, nullable=False, default="scheduled")
    refresh_cron: Mapped[str | None] = mapped_column(String, nullable=True, default="0 2 * * *")

    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_computed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    members: Mapped[list["SegmentMember"]] = relationship(back_populates="segment")


class SegmentMember(Base):
    __tablename__ = "segment_members"
    __table_args__ = {"schema": "cdp"}

    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.segments.id", ondelete="CASCADE"), primary_key=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.profiles.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    segment: Mapped["Segment"] = relationship(back_populates="members")
    profile: Mapped["Profile"] = relationship(back_populates="segment_memberships")  # noqa: F821
