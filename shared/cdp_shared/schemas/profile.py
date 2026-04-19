import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class IdentityOut(BaseModel):
    id: uuid.UUID
    id_type: str
    id_value: str
    source: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: uuid.UUID
    email: str | None
    phone: str | None
    loyalty_member_id: str | None
    sales_customer_id: str | None
    traits: dict[str, Any]
    is_anonymous: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileDetail(ProfileOut):
    identities: list[IdentityOut] = []


class PaginatedProfiles(BaseModel):
    items: list[ProfileOut]
    total: int
    page: int
    size: int
