import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column

from cdp_shared.db import Base


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = {"schema": "cdp"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    # admin | analyst | marketer
    role: Mapped[str] = mapped_column(String, nullable=False, default="analyst")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
