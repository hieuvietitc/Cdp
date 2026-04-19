from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventContext(BaseModel):
    page: dict[str, Any] | None = None
    locale: str | None = None
    timezone: str | None = None
    screen: dict[str, Any] | None = None
    user_agent: str | None = None
    ip: str | None = None
    sdk_version: str | None = None
    model_config = {"extra": "allow"}


class TrackEventIn(BaseModel):
    write_key: str
    anonymous_id: str
    user_id: str | None = None
    event: str  # Event name, e.g. "Booking Completed"
    event_type: Literal["track"] = "track"
    properties: dict[str, Any] = Field(default_factory=dict)
    context: EventContext = Field(default_factory=EventContext)
    timestamp: datetime | None = None
    session_id: str | None = None


class IdentifyEventIn(BaseModel):
    write_key: str
    anonymous_id: str
    user_id: str
    traits: dict[str, Any] = Field(default_factory=dict)
    context: EventContext = Field(default_factory=EventContext)
    timestamp: datetime | None = None


class PageEventIn(BaseModel):
    write_key: str
    anonymous_id: str
    user_id: str | None = None
    url: str | None = None
    title: str | None = None
    referrer: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    context: EventContext = Field(default_factory=EventContext)
    timestamp: datetime | None = None
    session_id: str | None = None


class BatchEventIn(BaseModel):
    write_key: str
    batch: list[TrackEventIn | IdentifyEventIn | PageEventIn]
