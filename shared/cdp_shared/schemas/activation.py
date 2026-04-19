import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class DestinationCreate(BaseModel):
    name: str
    type: Literal["sendgrid", "sms_esms", "meta_ads", "google_ads", "webhook"]
    config: dict[str, Any]


class DestinationOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivationCreate(BaseModel):
    segment_id: uuid.UUID
    destination_id: uuid.UUID
    trigger_type: Literal["manual", "scheduled", "realtime"] = "manual"


class ActivationOut(BaseModel):
    id: uuid.UUID
    segment_id: uuid.UUID
    destination_id: uuid.UUID
    trigger_type: str
    status: str
    profiles_sent: int
    errors: list
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
