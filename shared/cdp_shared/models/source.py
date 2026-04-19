import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column

from cdp_shared.db import Base


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # web | ios | android | server
    type: Mapped[str] = mapped_column(String, nullable=False)
    write_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
