import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, UUID, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cdp_shared.db import Base


class Identity(Base):
    __tablename__ = "identities"
    __table_args__ = (
        UniqueConstraint("id_type", "id_value", name="uq_identity_type_value"),
        {"schema": "cdp"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cdp.profiles.id", ondelete="CASCADE"), nullable=False
    )

    # anonymous_id | email | phone | loyalty_id | google_cid | fb_fbp | device_id | cookie_id
    id_type: Mapped[str] = mapped_column(String, nullable=False)
    id_value: Mapped[str] = mapped_column(String, nullable=False)

    # web_sdk | mobile_sdk | loyalty_batch | sales_batch | manual
    source: Mapped[str] = mapped_column(String, nullable=False)

    # 0.0–1.0; 1.0 = deterministic, <1.0 = probabilistic match
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="identities")  # noqa: F821
